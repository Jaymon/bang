# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re
from distutils import dir_util
import shutil
import types
import codecs
import datetime
import re
import logging

from .config import Config
from .path import Directory
from .utils import HTMLStripper, Template
from .md import Markdown


logger = logging.getLogger(__name__)



class Directories(object):
    """this is a simple linked list of DirectoryType instances, the Post instances have next_post
    and prev_post pointers that this class takes advantage of to build the list"""
    first_post = None
    total = 0
    last_post = None

    template_name = 'posts'
    """this is the template that will be used to compile the posts into html"""

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    def __init__(self, site):
        self.output_dir = site.output_dir
        self.site = site

    def append(self, post):
        if not self.first_post:
            self.first_post = post

        if self.last_post:
            post.prev_post = self.last_post
            self.last_post.next_post = post

        self.last_post = post
        self.total += 1

    def count(self):
        return self.total

    def __iter__(self):
        p = self.first_post
        while p:
            yield p
            p = p.next_post

    def __reversed__(self):
        p = self.last_post
        while p:
            yield p
            p = p.prev_post

    def reverse(self, count=0):
        """iterate backwards through the posts up to count"""
        p_count = 0
        for p in reversed(self):
            p_count += 1
            yield p

            if count and p_count >= count:
                break

    def matching(self, regex):
        """Iterate only through posts whose directory matches regex"""
        for p in self:
            if regex and not re.search(regex, str(p.input_dir), re.I):
                continue
            yield p

    def __len__(self):
        return self.total

    def output(self, **kwargs):
        """This will output an index.html file in the root directory

        **kwargs -- dict -- these will be passed to the template
        """
        logger.info("output Posts")
        output_dir = self.output_dir
        output_dir.create()

        output_file = os.path.join(str(output_dir), self.output_basename)

        # TODO -- generate both prev and next urls if needed

        logger.debug(
            'Templating Posts with template "{}" to output file {}'.format(
            self.template_name,
            output_file
        ))
        tmpl = Template(self.site.template_dir)
        tmpl.output(
            self.template_name,
            output_file,
            posts=self,
            config=self.site.config,
            site=self.site,
            **kwargs
        )

        # TODO -- after creating output_dir/index.html, then create output_dir/page/N
        # files for each page of Posts


class DirectoryType(Directory):

    list_class = Directories

    @property
    def config(self):
        return self.site.config

#     @classmethod
#     def plural_name(cls):
#         return "{}s".format(self.__class__.__name__.lower())

    @classmethod
    def match(cls, directory):
        raise NotImplementedError()

#     @classmethod
#     def append(cls, directory, site):
#         pname = cls.plural_name()
#         instances = getattr(site, pname, None)
#         if not instances:
#             instances = cls.list_class(site)
#             setattr(site, pname, instances)
# 
#         instance = cls(directory, site)
#         instances.append(instance)

    def __init__(self, input_dir, output_dir, site):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.site = site


class Other(DirectoryType):
    """Holds folders that are neither Aux or Post folders"""
    next_post = None
    """holds a pointer to the next Post"""

    prev_post = None
    """holds a pointer to the previous Post"""

    list_name = "others"

    def output(self, **kwargs):
        if self.input_dir.is_private(): return

        d = self.input_dir
        output_dir = self.output_dir

        output_dir.create()
        for f in d.files():
            output_dir.copy_file(f)

    @classmethod
    def match(cls, directory):
        return True


class Aux(Other):

    template_name = 'aux'
    """this is the template that will be used to compile the post into html"""

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    list_name = "auxs"

    @property
    def next_url(self):
        """returns the url of the next post"""
        p = self.next_post
        return p.url if p else ""

    @property
    def prev_url(self):
        """returns the url of the previous post"""
        p = self.prev_post
        return p.url if p else ""

    @property
    def modified(self):
        d = self.input_dir
        t = os.path.getmtime(d.content_file)
        modified = datetime.datetime.fromtimestamp(t)
        return modified

    @property
    def uri(self):
        """the path of the post (eg, /foo/bar/post-slug)"""
        d = self.input_dir
        relative = d.relative()
        relative = relative.replace('\\', '/')
        v = "/".join(['', relative])
        return v

    @property
    def url(self):
        """the full url of the post with host and everything"""
        base_url = self.site.config.base_url
        return u"{}{}".format(base_url, self.uri)

    @property
    def title(self):
        body = self.html
        title = ""

        # first try and get the title from a header tag in the body
        m = re.match(r"^\s*<h1[^>]*>([^<]*)</h1>", body, flags=re.I)
        if m:
            title = m.group(1).strip()

        if not title:
            # default to just the name of the directory this aux file lives in
            basename = os.path.basename(str(self.input_dir))
            title = basename.capitalize()

        return title

    @property
    def body(self):
        d = self.input_dir
        return d.file_contents(os.path.basename(d.content_file))

    @property
    def description(self):
        """Returns a nice description of the post, first 2 sentences"""
        #desc = getattr(self, "_description", None)
        desc = None
        if desc is None:
            html = self.html
            plain = HTMLStripper.strip_tags(html)
            ms = re.split("(?<=\S[\.\?!])(?:\s|$)", plain, maxsplit=2, flags=re.M)
            sentences = []
            for sentence in ms[0:2]:
                sentences.extend((s.strip() for s in sentence.splitlines() if s))
            desc = " ".join(sentences)
            self._description = desc

        return desc

    @property
    def image(self):
        """Return the image for the post, yes, this uses regex because I didn't want
        to rely on third party libraries to do this"""
        ret = ""
        html = self.html
        m = re.search("<img\s+[^>]+>", html, flags=re.M | re.I)
        if m:
            m = re.search("src=[\"\']([^\"\']+)", m.group(0), flags=re.I)
            if m:
                ret = m.group(1)
        return ret

    @property
    def meta(self):
        """return any meta-data this post has"""

        # this is kind of a crap way to do it but we need to parse the body to
        # make sure meta is parsed and available
        self.html 
        return getattr(self, "_meta", {})

    @property
    def html(self):
        """
        return html of the post

        base_url -- string -- if passed in, file links will be changed to base_url + post_url + filename

        return -- string -- rendered html
        """
        try:
            md = Markdown.get_instance()
            html = md.output(self)
            self._meta = md.Meta

        except AttributeError as e:
            # there might be attribute errors deep into Markdown that would
            # be suppressed if they bubbled up from here
            raise ValueError(e)

        return html

    @classmethod
    def match(cls, directory):
        ret_bool = False
        if directory.files(r'^index\.(md|markdown)$'):
            ret_bool = True
        return ret_bool

    def __str__(self):
        return self.input_dir.path

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        d = self.input_dir
        output_dir = self.output_dir
        output_file = os.path.join(str(output_dir), self.output_basename)
        logger.info("output {} to {}".format(self.title, output_file))

        r = output_dir.create()
        for input_file in d.other_files:
            output_dir.copy_file(input_file)

        # NOTE -- if there are other directories in the post directory, those are
        # considered "other directories" and so they will be copied over when the
        # others list is ran through and copied. This keeps duplicated work but
        # also isn't incredibly elegant, because if we ever just want to compile
        # one post, we would need to compile the post and any other directories
        # would need to be ran through separately

        #html = self.html
        self.output_file = output_file

        logger.debug(
            'Templating {} with template "{}" to output file {}'.format(
            d.content_file,
            self.template_name,
            output_file
        ))

        self.output_template(
            self.template_name,
            output_file,
            config=self.site.config,
            site=self.site,
            **kwargs
        )


    def output_template(self, template_name, output_file, **kwargs):
        kwargs[self.template_name] = self
        tmpl = Template(self.site.template_dir)
        tmpl.output(
            template_name,
            output_file,
            **kwargs
        )

    @classmethod
    def match(cls, directory):
        return True if directory.files(r'^index\.(md|markdown)$') else False


class Post(Aux):
    """this is a node in the Posts linked list, it holds all the information needed
    to output a Post in the input directory to the output directory"""
    template_name = 'post'

    list_name = "posts"

    @property
    def title(self):
        d = self.input_dir
        title = os.path.splitext(os.path.basename(d.content_file))[0]
        return title

    @classmethod
    def match(cls, directory):
        return True if directory.files(r'\.(md|markdown)$') else False

