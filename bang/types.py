# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re
import datetime
import re
import logging
import inspect

from datatypes.reflection import OrderedSubclasses
from datatypes import (
    Url,
    HTML,
    ContextNamespace,
)

from .compat import *
from .decorators import classproperty, once
from .path import Dirpath, Filepath
from .utils import ContextCache
from .event import event


logger = logging.getLogger(__name__)


class TypeIterator(object):
    """Iterate the passed in types"""
    def __init__(self, config, types):
        self.config = config
        self.types = types

    def reverse(self):
        for ts in self.get_types():
            for instance in reversed(ts):
                yield instance

    def __iter__(self):
        for ts in self.get_types():
            for instance in ts:
                yield instance

    def __reversed__(self):
        return self.reverse()

    def has(self):
        for ts in self.get_types():
            if ts:
                return True
        return False

    def get_types(self):
        for t in self.types:
            if t.name in self.config.project.types:
                yield self.config.project.types[t.name]


class PageIterator(TypeIterator):
    """like TypeIterator but will iterate through all config defined page_types"""
    def __init__(self, config):
        super().__init__(config, config.page_types)


class Types(object):
    first_instance = None
    """holds the head Type instance"""

    total = 0
    """holds how many Type instances have been appended to this container"""

    last_instance = None
    """holds the tail Type instance"""

    @classproperty
    def name(cls):
        return cls.__name__.lower()

    @property
    def head(self):
        return self.first_instance

    @property
    def tail(self):
        return self.last_instance

    def __init__(self, config):
        self.config = config

    def append(self, t):
        t.instances = self
        if not self.first_instance:
            self.first_instance = t

        if self.last_instance:
            t.prev_instance = self.last_instance
            self.last_instance.next_instance = t

        self.last_instance = t
        self.total += 1

    def count(self):
        return self.total

    def __iter__(self):
        t = self.first_instance
        while t:
            yield t
            t = t.next

    def __reversed__(self):
        return self.reverse()

    def reverse(self, count=0):
        """iterate backwards through the posts up to count"""
        t_count = 0
        t = self.last_instance
        while t:
            t_count += 1
            yield t
            t = t.prev
            if count and t_count >= count:
                break

    def chunk(self, limit, reverse=False):
        """chunk the total pages into limit chunks

        :param limit: int, the size of the chunks
        :param reverse: bool, if True then go from last_page to first_page, by
            default we go from first_page to last_page
        :returns: generator, yields chunks of at most limit size
        """
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

    def __len__(self):
        return self.total


class Pages(Types):
    """this is a simple container of Type instances, the Type instances have next_page
    and prev_type pointers that this class takes advantage of to build the list"""
    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    @classproperty
    def template_names(cls):
        """this is the template that will be used to compile the post into html"""
        ret = []
        for c in inspect.getmro(cls):
            if c is object: continue
            if hasattr(c, "name"):
                ret.append(c.name)
        return ret

    @property
    @once
    def template_name(self):
        theme = self.config.theme
        for template_name in self.template_names:
            logger.debug("Attempting to use template [{}.{}]".format(theme.name, template_name))
            if theme.has_template(template_name):
                return template_name

    def output(self, **kwargs):
        """This will output an index.html file in the root directory

        :param **kwargs: dict, these will be passed to the template
        """
        if self.config.output_dir.has_file(self.output_file):
            logger.warning(
                "Pages.output() cannot generate a root index.html file because one already exists"
            )
            return

        chunks = list(self.chunk(self.config.get("page_limit", 10), reverse=True))
        for page, pages in enumerate(chunks, 1):

            logger.info("output page {}".format(page))

            if page == 1:
                output_dir = self.config.output_dir
            else:
                output_dir = self.config.output_dir.child("page", String(page))
            output_dir.create()

            output_file = os.path.join(String(output_dir), self.output_basename)

            base_url = self.config.base_url

            kwargs["page"] = page
            # not sure which one I like more yet
            kwargs["pages"] = pages
            kwargs["instances"] = pages

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

            if len(chunks) > page:
                kwargs["prev_url"] = "{}/page/{}".format(base_url, page + 1)
                kwargs["prev_title"] = "Page {}".format(page + 1)

            self.output_template(output_file, **kwargs)

    def output_template(self, output_file, **kwargs):
        theme = self.config.theme

        logger.debug(
            'Templating Pages[{}] with theme.template [{}.{}] to output file {}'.format(
                kwargs.get("page", "unkown"),
                theme.name,
                self.template_name,
                output_file
            )
        )

        theme.output_template(
            self.template_name,
            output_file,
            **kwargs
        )


class Type(object):
    """Generic base class for types, a site is composed of different types, the 
    compile phase should check all the configured types's .match() method and the
    first .match() that returns True, that's what type the file is
    """
    next_instance = None
    """holds a pointer to the next Post"""

    prev_instance = None
    """holds a pointer to the previous Post"""

    instances_class = Types
    """Holds the aggregator class that will hold all instances of this type"""

    instances = None
    """contains a reference to the container class if the instance was appended
    to the container. This makes it possible for any Type instance to get the rest
    of the Type instances that were found"""

    @classproperty
    def name(cls):
        return cls.__name__.lower()

    @classmethod
    def match(cls, t):
        raise NotImplementedError()

    @property
    def uri(self):
        """the path of the post (eg, /foo/bar/post-slug)"""
        return Url(path=self.relpath)

    @property
    def url(self):
        """the full url of the post with host and everything"""
        base_url = self.config.base_url
        return Url(base_url, self.uri)

    @property
    def heading(self):
        """this will return something for a title no matter what, so even if the
        page doesn't have a title this will return something that is descriptive
        of the page

        :returns: string, some title
        """
        ret = self.title
        if not ret:
            ret = self.uri
        return ret

    def __init__(self, relpath, input_file, output_dir, config):
        """create an instance

        :param input_dir: Directory, this is the input directory of the actual
            type, not the project input dir
        :param output_dir: Directory, the output directory of the actual type, not
            the project output dir
        :param config: Config instance, useful for being able to populate information
            about the rest of the site on this page
        """
        self.relpath = relpath
        self.input_file = input_file
        self.output_dir = output_dir
        self.config = config

    def absolute_url(self, url):
        """normalizes the url into a full url using this Type as a base"""
        if not Url.is_url(url):
            config = self.config

            if Url.is_path_url(url):
                # a uri like /foo/bar is from root directory
                base_url = self.config.base_url

            else:
                # a uri like foo/bar is from this directory
                base_url = self.url

            url = Url(base_url, url)

        return url


class Other(Type):
    """The fallback Type, it's not really a page but is here to provide a 
    catch-all for any folders that don't match anything else, this type should
    always come last since it matches everything and its output() method just
    copies all the contents from input_dir to output_dir"""

    def output(self, **kwargs):
        self.input_file.copy_to(self.output_dir.child_file(self.input_file.basename))

    @classmethod
    def match(cls, filepath):
        return True


class Page(Other):
    """This is the generic page type, any index.md files will be this page type"""
    instances_class = Pages

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    @property
    def next_url(self):
        """returns the url of the next post"""
        p = self.next_instance
        return p.url if p else ""

    @property
    def prev_url(self):
        """returns the url of the previous post"""
        p = self.prev_instance
        return p.url if p else ""

    @property
    def modified(self):
        t = os.path.getmtime(self.input_file)
        modified = datetime.datetime.fromtimestamp(t)
        return modified

    @property
    def body(self):
        return self.input_file.read_text()

    @property
    def description(self):
        """Returns a nice description of the post, first 2 sentences"""
        #desc = getattr(self, "_description", None)
        desc = None
        if desc is None:
            plain = self.html.strip_tags(remove_tags=["figcaption", "sup", "div.footnote"])
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
    def markdown(self):
        return self.config.markdown

    @property
    def title(self):
        title, html, meta = self.compile()
        return title

    @property
    def html(self):
        """
        return html of the post

        base_url -- string -- if passed in, file links will be changed to base_url + post_url + filename

        return -- string -- rendered html
        """
        title, html, meta = self.compile()
        return HTML(html)

    @property
    def meta(self):
        """return any meta-data this post has"""

        # this is kind of a crap way to do it but we need to parse the body to
        # make sure meta is parsed and available
        title, html, meta = self.compile()
        return meta

    @property
    def template_name(self):
        theme = self.config.theme
        for template_name in self.template_names:
            logger.debug("Attempting to use theme.template [{}.{}]".format(theme.name, template_name))
            if theme.has_template(template_name):
                return template_name

    @classproperty
    def template_names(cls):
        """this is the template that will be used to compile the post into html"""
        ret = []
        subclasses = OrderedSubclasses(Type)
        subclasses.insert(cls)
        for c in subclasses[:-1]:
            if hasattr(c, "name"):
                ret.append(c.name)
        return ret

    @classmethod
    def regex(cls):
        return rf'^{cls.name}\.(md|markdown)$'

    @classmethod
    def match(cls, filepath):
        return bool(re.search(cls.regex(), filepath, flags=re.I))

    def compile(self):
        cache = getattr(self, "_cache", ContextNamespace(cascade=False))

        context_name = self.config.context_name()
        cache.switch_context(context_name)

        if "html" not in cache:
            logger.debug("Rendering html[{}]: {}".format(context_name, self.uri))

            try:
                #md = Markdown.get_instance()
                md = self.markdown
                html = md.output(self)
                meta = getattr(md, "Meta", {})

                title = meta.get("title", "")
                if not title:
                    m = re.match(r"^\s*<h1[^>]*>([^<]*)</h1>\s*", html, flags=re.I | re.M)
                    if m:
                        title = m.group(1).strip()

                        # we actually remove the title from the html since it will
                        # be available in .title
                        html = html[:m.start()] + html[m.end():]

                    else:
                        title = self.find_title(html)

                cache["html"] = html
                cache["meta"] = meta
                cache["title"] = title
                self._cache = cache

            except AttributeError as e:
                # there might be attribute errors deep into Markdown that would
                # be suppressed if they bubbled up from here
                logger.exception(e)
                raise ValueError(e) from e

        return cache["title"], cache["html"], cache["meta"]

    def find_title(self, html):
        """Find an appropriate title for this page, this is called in the .compile()
        method when a suitable title can't be found and it's a separate method
        call so children can override it

        :param html: string, the html of this page
        :returns: string, the title that will go into the .title property
        """
        return ""

    def __str__(self):
        output_relpath = self.output_dir.relative_to(self.config.output_dir)
        return f"{self.name}: {self.relpath} -> {output_relpath}/{self.output_basename}"

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        output_dir = self.output_dir
        output_file = output_dir.child_file(self.output_basename)
        #output_file = os.path.join(String(output_dir), self.output_basename)
        logger.info("output {} [{}] to {}".format(self.name, self.title, output_file))

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
        kwargs["prev_title"] = self.prev_instance.title if self.prev_instance else ""
        kwargs["next_url"] = self.next_url
        kwargs["next_title"] = self.next_instance.title if self.next_instance else ""

        self.output_template(
            output_file,
            **kwargs
        )

        # TODO -- output.page event?

    def output_template(self, output_file, theme=None, **kwargs):
        # not sure which one I like better yet
        kwargs["page"] = self
        kwargs["instance"] = self

        if not theme:
            theme = self.config.theme

        logger.info(
            'Templating input file {} with theme.template [{}.{}] to output file {}'.format(
                self.content_file,
                theme.name,
                self.template_name,
                output_file
            )
        )

        html = theme.render_template(
            self.template_name,
            **kwargs
        )

        # NOTE -- the .page is hardcoded instead of using something like
        # .template_name so plugins can rely on this event name always being
        # broadcast even if the templates can change (like a specific post
        # template)
        r = event.broadcast('output.template.page', self.config, html=HTML(html), instance=self)
        f = File(output_file, encoding=self.config.encoding)
        f.create(r.html)


