import sys
import os
import argparse
import shutil
from distutils import dir_util
import codecs
import fnmatch
import datetime
from operator import attrgetter
import re
import glob

import markdown
from jinja2 import Environment, FileSystemLoader

#from bang.server import Server
from server import Server

__version__ = "0.0.2"

class Template(object):
    def __init__(self, template_dir):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

        self.templates = {}
        for f in fnmatch.filter(os.listdir(self.template_dir), '*.html'):
            filename, fileext = os.path.splitext(f)
            self.templates[filename] = f

    def has(self, template_name):
        return template_name in self.templates

    def write(self, template, filepath, **kwargs):
        tmpl = self.env.get_template("{}.html".format(template))
        return tmpl.stream(**kwargs).dump(filepath)


def normalize_dir(d):
    """completely normalize a relative path (a path with ../, ./, or ~/)"""
    return os.path.abspath(os.path.expanduser(d))

def clear_dir(d):
    """this will clear a directory path of all files and folders"""
    dir_util.mkpath(d)
    for root, dirs, files in os.walk(d, topdown=True):
        for td in dirs:
            shutil.rmtree(os.path.join(root, td))

        for tf in files:
            os.unlink(os.path.join(root, tf))

        break

    return True

class Index(object):
    template = 'index'
    output_file = 'index.html'
    input_file = 'index'

    @property
    def body_filepath(self):
        v = getattr(self, '_body_filepath', None)
        if not v:
            v = os.path.join(self.input_dir, self.relative, self.body_file)
            self._body_filepath = v
        return v


    @property
    def modified(self):
        modified = getattr(self, '_modified', None)
        if not modified:
            t = os.path.getmtime(self.body_filepath)
            modified = datetime.datetime.fromtimestamp(t)
            self._modified = modified
        return modified

    @property
    def url(self):
        v = getattr(self, '_url', None)
        if not v:
            relative = self.relative_output
            relative = relative.replace('\\', '/')
            v = "/".join(['', relative])
            self._url = v
        return v

    @property
    def title(self):
        v = getattr(self, '_title', None)
        if not v:
            v = os.path.basename(self.relative)
            self._title = v
        return v

    @property
    def body(self):
        v = ''
        with codecs.open(self.body_filepath, 'r+', 'utf-8') as fp:
            v = fp.read()
        return v

    @property
    def html(self):
        body = self.body
        ext_callback = getattr(self, "normalize_{}".format(self.ext))
        html = ext_callback(body)
        return html

    @property
    def relative_output(self):
        v = getattr(self, '_relative_output', None)
        if not v:
            v = self.relative.lower()
            v = re.sub(ur'\s+', '-', v)
            self._relative_output = v
        return v

    @property
    def body_file(self):
        v = getattr(self, '_body_file', None)
        if not v:
            v, body_files = self.normalize_files()
            self._body_file = v
            self._files = body_files
        return v

    @property
    def files(self):
        v = getattr(self, '_files', None)
        if not v:
            body_file, v = self.normalize_files()
            self._body_file = body_file
            self._files = v
        return v

    def __init__(self, input_dir, relative):
        self.input_dir = input_dir
        self.relative = relative
        _, fileext = os.path.splitext(self.body_file)
        self.ext = fileext.lstrip('.')

    def normalize_md(self, text):
        return markdown.markdown(text)

    def normalize_html(self, text):
        return text

    def normalize_txt(self, text):
        return text

    def normalize_files(self):
        input_root = os.path.join(self.input_dir, self.relative)
        for _, _, files in os.walk(input_root, topdown=True):
            break

        body = None
        body_files = []
        pattern = "{}.*".format(self.input_file)
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                body = f

            else:
                body_files.append(f)

        return body, body_files

    def move_files(self, output_dir):
        dir_util.mkpath(os.path.join(output_dir, self.relative_output))
        for f in self.files:
            input_file = os.path.join(self.input_dir, self.relative, f)
            output_file = os.path.join(output_dir, self.relative_output, f)
            shutil.copy(input_file, output_file)

    def write(self, output_dir, tmpl, **template_kwargs):

        self.move_files(output_dir)

        output_file = os.path.join(output_dir, self.relative_output, self.output_file)
        tmpl.write(
            self.template,
            output_file,
            body=self.html,
            title=self.title,
            **template_kwargs
        )

        self.output_file = output_file

    @classmethod
    def is_type(cls, root):
        ret = False
        pattern = "{}.*".format(cls.input_file)
        for f in glob.iglob(os.path.join(root, pattern)):
            ret = True
        return ret


class Post(Index):
    input_file = 'post'


class Site(object):

    def __init__(self, input_dir, output_dir, template_dir):
        self.output_dir = normalize_dir(output_dir)
        self.input_dir = normalize_dir(input_dir)
        self.template_dir = normalize_dir(template_dir)
        self.tmpl = Template(self.template_dir)

        # clear the output directory
        clear_dir(self.output_dir)

        # go through and compile all the posts and other files
        self.posts = []
        self.indexes = []
        self.files = []
        for input_root, dirs, files in os.walk(self.input_dir, topdown=True):
            basename = os.path.basename(input_root)
            # ignore private dirs
            if basename.startswith('_'): continue

            relative = input_root.replace(self.input_dir, '').strip(os.sep)
            if Post.is_type(input_root):
                p = Post(
                    input_dir=self.input_dir,
                    relative=relative,
                )
                self.posts.append(p)

            elif Index.is_type(input_root):
                i = Index(
                    input_dir=self.input_dir,
                    relative=relative,
                )
                self.indexes.append(i)

            else:
                for f in files:
                    # ignore private files
                    if f.startswith('_'): continue
                    self.files.append(
                        (os.path.join(root, f), os.path.join(self.output_dir, relative, f))
                    )


        # sort the posts
        self.posts.sort(key=attrgetter('modified'), reverse=True)

    def write(self, **template_kwargs):
        # go through each post and write it out
        for i, p in enumerate(self.posts):

            prev_url = ''
            next_url = ''
            next_i = i - 1
            prev_i = i + 1
            if next_i >= 0:
                next_url = self.posts[next_i].url
            if prev_i < len(self.posts):
                prev_url = self.posts[prev_i].url

            p.write(
                self.output_dir,
                self.tmpl,
                prev_url=prev_url,
                next_url=next_url,
                **template_kwargs
            )

        for i in self.indexes:
            i.write(
                self.output_dir,
                self.tmpl
            )

        for input_file, output_file in self.files:
            d, _ = os.path.split(output_file)
            dir_util.mkpath(d)
            shutil.copy(input_file, output_file)

        # the latest post will be the index
        if self.posts:
            shutil.copy(self.posts[0].output_file, os.path.join(self.output_dir, 'index.html'))


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    parser = argparse.ArgumentParser(description='Bang - Static site generator')
    parser.add_argument(
        '--project-dir', '--dir', '-d',
        dest='project_dir',
        default=os.curdir,
        help='directory, defaults to current working directory'
    )
    parser.add_argument(
        '--output-dir', '-o',
        dest='output_dir',
        default=None,
        help='directory, defaults to project-dir/output'
    )
    parser.add_argument(
        '--template-dir', '-t',
        dest='template_dir',
        default=None,
        help='directory, defaults to project-dir/template'
    )
    parser.add_argument(
        '--port', '-p',
        dest='port',
        default=8000,
        type=int,
        help='the port for serve command'
    )
    parser.add_argument("-v", "--version", action='version', version="%(prog)s {}".format(__version__))
    parser.add_argument('command', nargs='?', default="compile")
    args = parser.parse_args()

    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join(args.project_dir, 'output')

    if args.command == 'compile':
        template_dir = args.template_dir
        if not template_dir:
            template_dir = os.path.join(args.project_dir, 'template')

        input_dir = os.path.join(args.project_dir, 'input')

        s = Site(input_dir, output_dir, template_dir)
        s.write()

    elif args.command == 'serve':
        s = Server(normalize_dir(output_dir), args.port)
        s.serve_forever()

    return 0


if __name__ == u'__main__':
    sys.exit(console())

