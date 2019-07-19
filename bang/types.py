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

from .decorators import classproperty
from .path import Directory
from .utils import HTMLStripper, Template
from .md import Markdown


logger = logging.getLogger(__name__)


class Types(object):
    """this is a simple linked list of Type instances, the Type instances have next_page
    and prev_type pointers that this class takes advantage of to build the list"""
    first_page = None
    total = 0
    last_page = None

    template_name = 'posts'
    """this is the template that will be used to compile the posts into html"""

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    @property
    def template(self):
        return Template(self.template_name, self.config.template_dir)

    def __init__(self, config):
        self.config = config

    def append(self, page):
        if not self.first_page:
            self.first_page = page

        if self.last_page:
            page.prev_page = self.last_page
            self.last_page.next_page = page

        self.last_page = page
        self.total += 1

    def count(self):
        return self.total

    def __iter__(self):
        p = self.first_page
        while p:
            yield p
            p = p.next_page

    def __reversed__(self):
        p = self.last_page
        while p:
            yield p
            p = p.prev_page

    def reverse(self, count=0):
        """iterate backwards through the posts up to count"""
        p_count = 0
        for p in reversed(self):
            p_count += 1
            yield p

            if count and p_count >= count:
                break

    def pages(self, limit, reverse=False):
        gen = reversed(self) if reverse else self
        interval = limit

        instances = []
        for count, p in enumerate(gen):
            if count >= limit:
                yield instances
                limit += interval
                instances = []
            instances.append(p)
        yield instances

    def matching(self, regex):
        """Iterate only through posts whose directory matches regex"""
        for p in self:
            if regex and not re.search(regex, str(p.input_dir), re.I):
                continue
            yield p

    def __len__(self):
        return self.total

    def output(self, pages=True, **kwargs):
        """This will output an index.html file in the root directory

        **kwargs -- dict -- these will be passed to the template
        """
        posts_pages = list(self.pages(self.config.get("page_limit", 10), reverse=True))
        for page, posts in enumerate(posts_pages, 1):

            logger.info("output page {}".format(page))

            if page == 1:
                output_dir = self.config.output_dir
            else:
                output_dir = self.config.output_dir.child("page", str(page))
            output_dir.create()

            output_file = os.path.join(str(output_dir), self.output_basename)

            base_url = self.config.base_url

            kwargs["prev_url"] = ""
            kwargs["prev_title"] = ""
            kwargs["next_url"] = ""
            kwargs["next_title"] = ""

            # ok, this is kind of confusing, but the linked list that holds
            # all the POSTS goes from left to right (0, 1, ..., N), so the
            # latest post would be all the way to the right. But the posts
            # pagination goes from right to left (N, N-1, ..., 0) so we need
            # to reverse the prev and next urls so they match the post
            # linked list and stay consistent on the site, so if you are on
            # page 2 then page 1 would be the next url and page 3 would be
            # the previous url
            if page - 1:
                if page - 1 == 1:
                    kwargs["next_url"] = base_url
                    kwargs["next_title"] = "Go Home"

                else:
                    kwargs["next_url"] = "{}/page/{}".format(base_url, page - 1)
                    kwargs["next_title"] = "Page {}".format(page - 1)

            if len(posts_pages) > page:
                kwargs["prev_url"] = "{}/page/{}".format(base_url, page + 1)
                kwargs["prev_title"] = "Page {}".format(page + 1)

            logger.debug(
                'Templating Posts[{}] with template "{}" to output file {}'.format(
                page,
                self.template_name,
                output_file
            ))

            self.template.output(
                output_file,
                posts=posts,
                config=self.config,
                **kwargs
            )


class Type(object):
    """Generic base class for types, a site is composed of different types, the 
    compile phase should check all the types's .match() method and the first call
    that returns True, that's what type the folder/file is"""
    next_page = None
    """holds a pointer to the next Post"""

    prev_page = None
    """holds a pointer to the previous Post"""

    list_class = Types
    """Holds the aggregator class that will hold all instances of this type"""

    @classproperty
    def list_name(cls):
        return "{}s".format(cls.__name__.lower())

    @classmethod
    def match(cls, t):
        raise NotImplementedError()

    def __init__(self, input_dir, output_dir, config):
        """create an instance

        :param input_dir: Directory, this is the input directory of the actual
            type, not the project input dir
        :param output_dir: Directory, the output directory of the actual type, not
            the project output dir
        :param config: Config instance, useful for being able to populate information
            about the rest of the site on this page
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config


class DirectoryType(Type, Directory):
    """The base class for a directory type, which handles checking directories
    that match certain format, if it finds a directory that matches then that
    directory will be considered the type of whatever matched it and no files
    or subdirectories within that directory would be traversed"""
    pass


class Other(DirectoryType):
    """Holds folders that are neither Aux or Post folders"""

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

    regex = r'^index\.(md|markdown)$'

    @property
    def content_file(self):
        d = self.input_dir
        for f in d.files(self.regex):
            break
        return f

    @property
    def other_files(self):
        d = self.input_dir
        for f in d.files():
            if not re.search(self.regex, f, re.I):
                yield f

    @property
    def template(self):
        return Template(self.template_name, self.config.template_dir)

    @property
    def next_url(self):
        """returns the url of the next post"""
        p = self.next_page
        return p.url if p else ""

    @property
    def prev_url(self):
        """returns the url of the previous post"""
        p = self.prev_page
        return p.url if p else ""

    @property
    def modified(self):
        t = os.path.getmtime(self.content_file)
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
        base_url = self.config.base_url
        return "{}{}".format(base_url, self.uri)

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
        return self.input_dir.file_contents(os.path.basename(self.content_file))

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
    def markdown(self):
        return Markdown.get_instance()
#         md = getattr(self, "_markdown", None)
#         if not md:
#             md = Markdown.create_instance()
#             self._markdown = md
#         return md

    @property
    def html(self):
        """
        return html of the post

        base_url -- string -- if passed in, file links will be changed to base_url + post_url + filename

        return -- string -- rendered html
        """
        context_name = self.config.context_name
        htmls = getattr(self, "_htmls", {})
        html = htmls.get(context_name, "")
        if not html:
            logger.debug("Rendering html[{}]: {}".format(context_name, self.input_dir.basename))
            try:
                #md = Markdown.get_instance()
                md = self.markdown
                html = md.output(self)
                self._meta = md.Meta
                htmls[context_name] = html
                self._htmls = htmls

            except AttributeError as e:
                # there might be attribute errors deep into Markdown that would
                # be suppressed if they bubbled up from here
                logger.exception(e)
                raise ValueError(e)

        return html

    def __str__(self):
        return self.input_dir.path

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        output_dir = self.output_dir
        output_file = os.path.join(str(output_dir), self.output_basename)
        logger.info("output {} to {}".format(self.title, output_file))

        r = output_dir.create()
        for input_file in self.other_files:
            output_dir.copy_file(input_file)

        # NOTE -- if there are other directories in the post directory, those are
        # considered "other directories" and so they will be copied over when the
        # others list is ran through and copied. This keeps duplicated work but
        # also isn't incredibly elegant, because if we ever just want to compile
        # one post, we would need to compile the post and any other directories
        # would need to be ran through separately

        #html = self.html
        self.output_file = output_file

        kwargs["prev_url"] = self.prev_url
        kwargs["prev_title"] = self.prev_page.title if self.prev_page else ""
        kwargs["next_url"] = self.next_url
        kwargs["next_title"] = self.next_page.title if self.next_page else ""

        logger.debug(
            'Templating {} with template "{}" to output file {}'.format(
            self.content_file,
            self.template_name,
            output_file
        ))

        self.output_template(
            output_file,
            config=self.config,
            **kwargs
        )

    def output_template(self, output_file, **kwargs):
        kwargs[self.template_name] = self
        self.template.output(
            output_file,
            **kwargs
        )

    @classmethod
    def match(cls, directory):
        return True if directory.files(cls.regex) else False


class Post(Aux):
    """this is a node in the Posts linked list, it holds all the information needed
    to output a Post in the input directory to the output directory"""
    template_name = 'post'

    regex = r'\.(md|markdown)$'

    @property
    def title(self):
        title = os.path.splitext(os.path.basename(self.content_file))[0]
        return title

    @classmethod
    def match(cls, directory):
        return True if directory.files(cls.regex) else False

