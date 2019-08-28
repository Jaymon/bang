# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import sys
import re
from distutils import dir_util
import shutil
import codecs
import logging
import fnmatch
import struct
import imghdr

from .compat import *
from .event import event


logger = logging.getLogger(__name__)


class Path(object):
    """Parent class containing common methods for File and Directory"""

    @property
    def basename(self):
        return os.path.basename(self.path)

    def __init__(self, *bits):
        self.path = ''
        self.ancestor_dir = None
        if bits:
            bits = list(String(b) for b in bits)
            bits[0] = self.normalize(bits[0])
            for i in xrange(1, len(bits)):
                bits[i] = bits[i].strip('\\/')
            self.path = os.path.join(*bits)

    @classmethod
    def normalize(cls, d):
        """completely normalize a relative path (a path with ../, ./, or ~/)"""
        return os.path.abspath(os.path.expanduser(str(d)))

    def __str__(self):
        return ByteString(self.path) if is_py2 else self.__unicode__()

    def __unicode__(self):
        return String(self.path)

    def is_private(self):
        basename = self.basename
        return basename.startswith("_") or basename.startswith(".")

    def in_private(self):
        """make sure this path isn't an any private directory"""
        ret = False
        path = self.path
        while path:
            path, basename = os.path.split(path)
            if basename.startswith('_'):
                ret = True
                break
        return ret

    def relative(self, ancestor_dir=None):
        """
        returns the relative bits to the parent_dir

        :Example:
            d = Directory("/foo/bar/baz/che")
            d.relative("/foo/bar") # baz/che
            d.relative("/foo") # bar/baz/che

        :param ancestor_dir: string|Directory, the directory you want to return that self
            is a child of, if ancestor_dir is empty then it will use self.ancestor_dir
        :returns: string, the part of the path that is relative
        """
        if not ancestor_dir:
            ancestor_dir = self.ancestor_dir
        if not ancestor_dir:
            raise ValueError("no ancestor_dir found")

        relative = self.path.replace(String(ancestor_dir), '', 1).strip(os.sep).strip("/")
        return relative
    relative_to=relative

    def relative_parts(self, ancestor_dir=None):
        relative = self.relative(ancestor_dir)
        return re.split(r"[\/]", relative)
    parts_relative_to=relative_parts

    def clone(self):
        """return a new instance with the same path"""
        d = type(self)(self.path)
        d.ancestor_dir = self.ancestor_dir
        return d


class File(Path):

    @property
    def ext(self):
        """return the extension of the file, the basename without the fileroot"""
        return os.path.splitext(self.basename)[1].lstrip(".")
    extension = ext

    @property
    def fileroot(self):
        """return the basename without the extension"""
        return os.path.splitext(self.basename)[0]

    @property
    def directory(self):
        """return the directory portion of a directory/fileroot.ext path"""
        return Directory(os.path.dirname(self.path))

    def __init__(self, *bits, **kwargs):
        self.encoding = kwargs.pop("encoding", "UTF-8")
        super(File, self).__init__(*bits)

    def exists(self):
        return os.path.isfile(self.path)

    def contents(self, encoding=""):
        contents = ""
        try:
            with self.open(encoding=encoding) as f:
            #with codecs.open(self.path, encoding=encoding, mode='r+') as f:
                contents = f.read()
        except IOError:
            # ignore file does not exist errors
            pass

        return contents

    def create(self, contents, encoding=""):
        """create the file with basename in this directory with contents"""
        logger.debug("create file {}".format(self.path))
        encoding = encoding or self.encoding

        # make sure directory exists
        d = self.directory
        d.create()

        oldmask = os.umask(0)
        if encoding:
            f = self.open(mode="w+", encoding=encoding)
        else:
            # https://docs.python.org/2.7/library/functions.html#open
            f = self.open(mode="w+b")

        f.write(contents)
        f.close()
        oldmask = os.umask(oldmask)
        self.encoding = encoding
        return self

    def copy_to(self, output_dir):
        basename = self.basename
        output_file = File(output_dir, basename)
        logger.debug("copy file {} to {}".format(self.path, output_file))
        return File(shutil.copy(String(self.path), String(output_file)))

    def open(self, mode="", encoding=""):
        """open the file"""
        encoding = encoding or self.encoding
        if not mode:
            mode = "r" if encoding else "rb"

        if encoding:
            return codecs.open(self.path, encoding=encoding, mode=mode)

        else:
            return open(self.path, mode=mode)


class Image(File):
    @property
    def width(self):
        width, height = self.dimensions
        return width

    @property
    def height(self):
        width, height = self.dimensions
        return height

    @property
    def dimensions(self):
        return self.get_info()["dimensions"][-1]

    def __init__(self, *bits):
        super(Image, self).__init__(*bits, encoding="")

    def sizes(self):
        sizes = []
        info = self.get_info()
        for width, height in info["dimensions"]:
            sizes.append("{}x{}".format(width, height))
        return " ".join(sizes)

    def get_info(self):
        info = getattr(self, "_info", None)
        if info:
            return info

        # this makes heavy use of struct: https://docs.python.org/3/library/struct.html
        # based on this great answer on SO: https://stackoverflow.com/a/39778771/5006
        # read/write ico files: https://github.com/grigoryvp/pyico

        info = {"dimensions": [], "what": ""}

        with self.open() as fp:
            head = fp.read(24)
            if len(head) != 24:
                raise ValueError("Could not understand image")

            # https://docs.python.org/2.7/library/imghdr.html
            what = imghdr.what(None, head)
            if what is None:
                what = self.extension

            if what == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    raise ValueError("Could not understand PNG image")

                width, height = struct.unpack('>ii', head[16:24])
                info["dimensions"].append((width, height))

            elif what == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
                info["dimensions"].append((width, height))

            elif what == 'jpeg':
                try:
                    fp.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf or ftype in (0xc4, 0xc8, 0xcc):
                        fp.seek(size, 1)
                        byte = fp.read(1)
                        while ord(byte) == 0xff:
                            byte = fp.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', fp.read(2))[0] - 2
                    # We are at a SOFn block
                    fp.seek(1, 1)  # Skip `precision' byte.
                    height, width = struct.unpack('>HH', fp.read(4))
                    info["dimensions"].append((width, height))

                except Exception: #W0703
                    raise

            elif what == "ico":
                # https://en.wikipedia.org/wiki/ICO_(file_format)#Outline
                fp.seek(0)
                reserved, image_type, image_count = struct.unpack('<HHH', fp.read(6))
#                 reserved = struct.unpack('<H', fp.read(2))
#                 image_type = struct.unpack('<H', fp.read(2))[0]
#                 image_count = struct.unpack('<H', fp.read(2))[0]

                for x in range(image_count):
                    width = struct.unpack('<B', fp.read(1))[0] or 256
                    height = struct.unpack('<B', fp.read(1))[0] or 256
                    info["dimensions"].append((width, height))

                    fp.read(6) # we don't care about color or density info
                    size = struct.unpack('<I', fp.read(4))[0]
                    offset = struct.unpack('<I', fp.read(4))[0]

            else:
                raise ValueError("Unsupported image type {}".format(self.extension))

            info["what"] = what
            self._info = info
            return info
            #return width, height

    def is_favicon(self):
        info = self.get_info()
        return info["what"] == "ico"

    def is_animated(self):
        """Return true if image is an animated gif

        :returns: boolean, True if the image is an animated gif
        """
        return self.is_animated_gif()

    def is_animated_gif(self):
        """Return true if image is an animated gif

        primarily used this great deep dive into the structure of an animated gif
        to figure out how to parse it:

            http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp

        Other links that also helped:

            https://en.wikipedia.org/wiki/GIF#Animated_GIF
            https://www.w3.org/Graphics/GIF/spec-gif89a.txt
            https://stackoverflow.com/a/1412644/5006

        :returns: boolean, True if the image is an animated gif
        """
        info = self.get_info()
        if info["what"] != "gif": return False

        ret = False
        image_count = 0

        def skip_color_table(fp, packed_byte):
            """this will fp.seek() completely passed the color table

            http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#global_color_table_block

            :param fp: io, the open image file
            :param packed_byte: the byte that tells if the color table exists and 
                how big it is
            """
            if is_py2:
                packed_byte = int(packed_byte.encode("hex"), 16)
            # https://stackoverflow.com/a/13107/5006
            has_gct = (packed_byte & 0b10000000) >> 7
            gct_size = packed_byte & 0b00000111

            if has_gct:
                global_color_table = fp.read(3 * pow(2, gct_size + 1))
                #pout.v(" ".join("{:02x}".format(ord(c)) for c in global_color_table))

        def skip_image_data(fp):
            """skips the image data, which is basically just a series of sub blocks
            with the addition of the lzw minimum code to decompress the file data

            http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#image_data_block

            :param fp: io, the open image file
            """
            lzw_minimum_code_size = fp.read(1)
            skip_sub_blocks(fp)

        def skip_sub_blocks(fp):
            """skips over the sub blocks

            the first byte of the sub block tells you how big that sub block is, then
            you read those, then read the next byte, which will tell you how big
            the next sub block is, you keep doing this until you get a sub block
            size of zero

            :param fp: io, the open image file
            """
            num_sub_blocks = ord(fp.read(1))
            while num_sub_blocks != 0x00:
                fp.read(num_sub_blocks)
                num_sub_blocks = ord(fp.read(1))

        with self.open() as fp:
            header = fp.read(6)
            #pout.v(header)
            if header == b"GIF89a": # GIF87a doesn't support animation
                logical_screen_descriptor = fp.read(7)
                #pout.v(" ".join("{:02x}".format(ord(c)) for c in logical_screen_descriptor))
                #pout.v(bytearray(logical_screen_descriptor))
                #pout.v(logical_screen_descriptor.encode("hex"))
                skip_color_table(fp, logical_screen_descriptor[4])

                b = ord(fp.read(1))
                while b != 0x3B: # 3B is always the last byte in the gif
                    if b == 0x21: # 21 is the extension block byte
                        b = ord(fp.read(1))
                        if b == 0xF9: # graphic control extension
                            # http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#graphics_control_extension_block
                            block_size = ord(fp.read(1))
                            fp.read(block_size)
                            b = ord(fp.read(1))
                            if b != 0x00:
                                raise ValueError("GCT should end with 0x00")

                        elif b == 0xFF: # application extension
                            # http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#application_extension_block
                            block_size = ord(fp.read(1))
                            fp.read(block_size)
                            skip_sub_blocks(fp)

                        elif b == 0x01: # plain text extension
                            # http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#plain_text_extension_block
                            block_size = ord(fp.read(1))
                            fp.read(block_size)
                            skip_sub_blocks(fp)

                        elif b == 0xFE: # comment extension
                            # http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#comment_extension_block
                            skip_sub_blocks(fp)

                    elif b == 0x2C: # Image descriptor
                        # http://www.matthewflickinger.com/lab/whatsinagif/bits_and_bytes.asp#image_descriptor_block
                        image_count += 1
                        if image_count > 1:
                            # if we've seen more than one image it's animated so
                            # we're done
                            ret = True
                            break

                        # total size is 10 bytes, we already have the first byte so
                        # let's grab the other 9 bytes
                        image_descriptor = fp.read(9)
                        skip_color_table(fp, image_descriptor[-1])
                        skip_image_data(fp)

                    b = ord(fp.read(1))

        return ret


class Directory(Path):

    def exists(self):
        return os.path.isdir(self.path)

    def file_contents(self, *bits):
        """return the contents of the basename file in this directory"""
        contents = ""
        output_file = File(self.path, *bits)
        return output_file.contents()

    def create_file(self, basename, contents, encoding=""):
        """create the file with basename in this directory with contents"""
        output_file = File(self.path, basename, encoding=encoding)
        return output_file.create(contents)

    def copy_file(self, input_file):
        """copy the input_file to this directory"""
        return File(input_file).copy_to(self.path)

    def copy_paths(self, output_dir, depth=0):
        """you have current directory self and you want to copy the entire directory
        tree of self into output_dir, this finds all the subdirectories of self and
        creates an equivalent path in output_dir

        :param output_dir: Directory, the directory you want to copy the tree of this
            Directory (self) into
        :returns: yields tuples of (input_subdir, output_subdir)
        """
        input_dir = self.clone()
        input_dir.ancestor_dir = self
        output_dir = Directory(output_dir).clone()
        yield input_dir, output_dir

        for input_subdir in input_dir.directories(depth=depth):
            parts = input_subdir.relative_parts()
            is_valid = not depth or len(parts) < depth

            if is_valid:
                output_subdir = output_dir / input_subdir.relative()
                yield input_subdir, output_subdir

    def copy_to(self, output_dir, depth=0):
        """Copies to depth of the directory tree of self to output_dir

        :param output_dir: Directory, the directory you want to copy the tree of this
            Directory (self) into
        :param depth: int, if 0 then copies the entire directory tree, if 1 then
            only copies the files in self.path, if 2 then would copy immediate .path
            and one more level, etc.
        """
        for input_subdir, output_subdir in self.copy_paths(output_dir, depth=depth):
            #if input_subdir.is_private(): continue
            output_subdir.create()
            for f in input_subdir.files():
                output_subdir.copy_file(f)

    def create(self):
        """create the directory path"""
        logger.debug("create dir: {}".format(self.path))
        # https://docs.python.org/2.5/dist/module-distutils.dirutil.html
        return dir_util.mkpath(self.path)

    def clear(self):
        """this will clear a directory path of all files and folders"""
        # http://stackoverflow.com/a/1073382/5006
        logger.debug("clearing {}".format(self.path))
        dir_util.mkpath(self.path)
        for root, dirs, files in os.walk(self.path, topdown=True):
            for td in dirs:
                shutil.rmtree(os.path.join(root, td))

            for tf in files:
                os.unlink(os.path.join(root, tf))

            break

        # clear dir_util's internal cache otherwise calling create() again in same run
        # won't actually create the directory and won't tell you it didn't create it and
        # there doesn't seem to be an "official" way to clear the cache
        # https://hg.python.org/cpython/file/2.7/Lib/distutils/dir_util.py#l14
        dir_util._path_created = {}
        return True

    def child(self, *bits):
        """Return a new instance with bits added onto self's path"""
        ret = Directory(self.path, *bits)
        if not os.path.isdir(ret.path):
            if os.path.isfile(ret.path):
                ret = File(ret.path)
        return ret

    def child_file(self, *bits):
        return File(self.path, *bits)

    def child_directory(self, *bits):
        return Directory(self.path, *bits)

    def __div__(self, bits):
        if isinstance(bits, basestring):
            bits = [bits]
        else:
            bits = list(bits)
        return self.child(*bits)

    def __truediv__(self, bits):
        return self.__div__(bits)

    def __iter__(self):
        for d in self.directories(depth=0):
            yield d

    def files(self, regex=None, depth=1, exclude=False):
        """return files in self

        :param regex: string, the regular expression
        :param depth: int, if 1, just return immediate files, if 0 return all files
            of the entire tree, otherwise just return depth files
        :param exclude: bool, if True then any files that would be returned won't
            and files that wouldn't be returned normally will be
        :returns: list, the matching files
        """
        fs = []
        for root_dir, subdirs, files in os.walk(self.path, topdown=True):
            for basename in files:
                f = File(root_dir, basename)
                if not f.is_private():
                    if exclude:
                        if regex and not re.search(regex, basename, re.I):
                            fs.append(f.path)

                    else:
                        if not regex or re.search(regex, basename, re.I):
                            fs.append(f.path)


            fs.sort()
            if depth != 1:
                fs2 = []
                depth = depth - 1 if depth else depth
                for sd in subdirs:
                    d = Directory(root_dir, sd)
                    if not d.is_private():
                        fs2.extend(d.files(regex=regex, depth=depth))
                fs.extend(fs2)

            break

        return fs

    def directories(self, regex=None, depth=1):
        """return directories in self

        :param regex: string, the regular expression
        :param depth: int, if 1, just return immediate dirs, if 0 return all subdirs
            of the entire tree, otherwise just return depth dirs
        :returns: list, the matching directories
        """
        ds = []
        for root_dir, dirs, _ in os.walk(self.path, topdown=True):
            for basename in dirs:
                if not regex or re.search(regex, basename, re.I):
                    d = Directory(root_dir, basename)
                    d.ancestor_dir = self
                    if not d.is_private():
                        ds.append(d)

            ds.sort(key=lambda d: d.path)
            if depth != 1:
                ds2 = []
                depth = depth - 1 if depth else depth
                for d in ds:
                    for sd in d.directories(regex=regex, depth=depth):
                        sd.ancestor_dir = self
                        ds2.append(sd)

                ds.extend(ds2)

            break

        return ds

    def glob(self, pattern):
        """
        glob the immediate directory for pattern

        :param pattern: string, something like '*.html'
        """
        for f in fnmatch.filter(os.listdir(String(self.path)), pattern):
            yield f

    def has_file(self, *bits):
        """return true if the file basename exists in this directory"""
        return File(self.path, *bits).exists()

    def has_directory(self, *bits):
        d = self.child(*bits)
        return d.exists()

    def has_index(self):
        """returns True if this directory has an index.* file already"""
        r = False
        for f in self.files(r'^index\.'):
            r = True
            break

        return r


class DataDirectory(Directory):
    def __init__(self):
        base_dir = os.path.dirname(sys.modules[__name__.split(".")[0]].__file__)
        super(DataDirectory, self).__init__(base_dir, "data")

    def themes_directory(self):
        return self.child_directory("themes")

    def project_directory(self):
        return self.child_directory("project")


# class TemplateDirectory(Directory):
#     """Thin wrapper around Jinja functionality that handles templating things
# 
#     http://jinja.pocoo.org/docs/dev/
#     https://jinja.palletsprojects.com/en/master/api/
#     https://jinja.palletsprojects.com/en/2.10.x/
# 
#     template documentation:
#         https://jinja.palletsprojects.com/en/2.10.x/templates/
#     """
#     def __init__(self, template_dir):
#         self.path = template_dir
#         # https://jinja.palletsprojects.com/en/master/api/#jinja2.Environment
#         self.env = Environment(
#             loader=FileSystemLoader(String(self.path)),
#             #extensions=['jinja2.ext.with_'] # http://jinja.pocoo.org/docs/dev/templates/#with-statement
#             lstrip_blocks=True,
#             trim_blocks=True,
#         )
# 
#         self.templates = {}
#         for f in self.path.files(regex=r"\.html$", depth=0):
#             filename, fileext = os.path.splitext(File(f).relative(self.path))
#             self.templates[filename] = f
# 
#     def has(self, template_name):
#         return template_name in self.templates
# 
#     def render(self, template_name, filepath, config, **kwargs):
#         """
#         https://jinja.palletsprojects.com/en/master/api/#jinja2.Template.render
#         """
#         tmpl = self.env.get_template("{}.html".format(template_name))
#         html = tmpl.render(config=config, **kwargs)
#         r = event.broadcast('output.template', config, html=HTML(html))
#         return r.html
# 
#     def create(self, filepath, config, html):
#         f = File(filepath, encoding=config.encoding)
#         f.create(html)
# 
#     def output(self, template_name, filepath, config, **kwargs):
#         """output kwargs using the template template_name to filepath
# 
#         :param template_name: string, the template you want to use for kwargs
#         :param filepath: string, the destination file that will be output to
#         :param config: Config instance
#         :param **kwargs: dict, all these will be passed to the template
#         """
#         html = self.render(template_name, filepath, config, **kwargs)
#         self.create(filepath, config, html)
#         #return tmpl.stream(config=config, **kwargs).dump(String(filepath), encoding=config.encoding)
# 
# 
