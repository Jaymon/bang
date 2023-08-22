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
    AppendList,
    OrderedList,
    property as cachedproperty,
    Datetime,
)

from .compat import *
from .decorators import classproperty, once
from .path import Dirpath, Filepath
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


class Types(OrderedList):
    @classproperty
    def name(cls):
        return cls.__name__.lower()

    def __init__(self, config):
        self.config = config
        super().__init__()

    def key(self, t):
        """Used to keep order"""
        return t.input_dir

    def inserted(self, i, t):
        if i is None:
            try:
                t.prev_instance = self[-2]
                self[-2].next_instance = t

            except IndexError:
                pass

        else:
            try:
                t.next_instance = self[i + 1]
                self[i + 1].prev_instance = t

            except IndexError:
                pass

            try:
                t.prev_instance = self[i - 1]
                self[i - 1].next_instance = t

            except IndexError:
                pass

    def append(self, t):
        t.instances = self
        super().append(t)

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


class Pages(Types):
    """this is a simple container of Type instances, the Type instances have
    next_page and prev_type pointers that this class takes advantage of to build
    the list
    """
    @classproperty
    def template_names(cls):
        """this is the template that will be used to compile the post into html"""
        ret = []
        for c in inspect.getmro(cls):
            if c is object: continue
            if hasattr(c, "name"):
                ret.append(c.name)
        return ret

    @cachedproperty(cached="_template_name")
    def template_name(self):
        theme = self.config.theme
        for template_name in self.template_names:
            logger.debug("Attempting to use template [{}.{}]".format(
                theme.name,
                template_name
            ))
            if theme.has_template(template_name):
                return template_name

    def output(self, output_dir="", **kwargs):
        """This will output an index.html file in the root directory

        :param output_dir: Dirpath, this is the directory to output index files
            to. If this isn't passed in then it will default to
            self.config.output_dir
        :param **kwargs: dict, these will be passed to the template
        """
        output_basename = self.config.page_output_basename
        output_dir = Dirpath(output_dir or self.config.output_dir)
        base_url = self.config.base_url.child(
            output_dir.relative_to(self.config.output_dir)
        )

        if output_dir.has_file(output_basename):
            logger.warning(
                "Pages.output() cannot generate a root index.html file because one already exists"
            )
            return

        chunks = list(self.chunk(self.config.get("page_limit", 10), reverse=True))
        for page_index, pages in enumerate(chunks, 1):

            logger.info(f"output page {page_index}")

            if page_index == 1:
                page_output_file = output_dir.child_file(output_basename)

            else:
                page_output_file = output_dir.child_file(
                    "page",
                    page_index,
                    output_basename
                )

            kwargs["page_index"] = page_index
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
            if page_index - 1:
                if page_index - 1 == 1:
                    kwargs["next_url"] = base_url or "/"
                    kwargs["next_title"] = "Go Home"

                else:
                    kwargs["next_url"] = base_url.child("page", page_index - 1)
                    kwargs["next_title"] = "Page {}".format(page_index - 1)

            if len(chunks) > page_index:
                kwargs["prev_url"] = base_url.child("page", page_index + 1)
                kwargs["prev_title"] = "Page {}".format(page_index + 1)

            self.output_template(page_output_file, **kwargs)

    def output_template(self, output_file, **kwargs):
        theme = self.config.theme

        logger.debug(
            'Templating Pages[{}] with theme.template [{}.{}] to output file {}'.format(
                kwargs.get("page", "unknown"),
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

    classes = None
    """Holds the deifned Type subclasses that have been loaded into memory. See
    .__init_subclasses__() and self.config.types"""

    @classproperty
    def name(cls):
        return cls.__name__.lower()

    @classmethod
    def match(cls, t):
        raise NotImplementedError()

    @property
    def input_dir(self):
        return self.input_file.parent

    @property
    def output_file(self):
        return self.output_dir.child_file(self.input_file.basename)

    @property
    def uri(self):
        """the path of the file (eg, /foo/bar/basename.ext)"""
        relpath = self.output_file.relative_to(self.config.output_dir)
        return Url(path=relpath)

    @property
    def url(self):
        """the full url of the post with host and everything"""
        base_url = self.config.base_url
        return Url(base_url, self.uri)

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
    def created(self):
        return self.input_file.created()

    @property
    def modified(self):
        return self.input_file.modified()
        #return Datetime(os.path.getmtime(self.input_file))

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

    def __init__(self, input_file, output_dir, config):
        """create an instance

        :param input_file: Filepath, this is the input file (page.md) of the
            actual type
        :param output_dir: Directory, the output directory of the actual type,
            not the project output dir
        :param config: Config instance, useful for being able to populate
            information about the rest of the site on this page
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.config = config

    def __init_subclass__(cls, *args, **kwargs):
        """
        https://peps.python.org/pep-0487/
        """
        super().__init_subclass__(*args, **kwargs)

        if not Type.classes:
            Type.classes = OrderedSubclasses(Type)

        # https://github.com/Jaymon/bang/issues/61
        Type.classes.insert(cls)

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

    def __str__(self):
        #input_relpath = self.input_file.relative_to(self.config.input_dir)
        output_relpath = self.output_file.relative_to(self.config.output_dir)
        #return f"{self.name}: {input_relpath} -> {output_relpath}"
        return f"{self.name}: {self.input_file} -> {output_relpath}"


class Other(Type):
    """The fallback Type, it's not really a page but is here to provide a 
    catch-all for any folders that don't match anything else, this type should
    always come last since it matches everything and its output() method just
    copies all the contents from input_dir to output_dir"""

    def output(self, **kwargs):
        logger.info(f"output {self}")
        self.input_file.copy_to(self.output_file)

    @classmethod
    def match(cls, filepath):
        return True


class Page(Other):
    """This is the generic page type, any index.md files will be this page type"""
    instances_class = Pages

    @property
    def next_title(self):
        """returns the title of the next post"""
        p = self.next_instance
        return p.title if p else ""

    @property
    def prev_title(self):
        """returns the title of the previous post"""
        p = self.prev_instance
        return p.title if p else ""

    @property
    def uri(self):
        """the path of the post (eg, /foo/bar/post-slug)"""
        relpath = self.output_dir.relative_to(self.config.output_dir)
        return Url(path="/" if relpath == "." else "/" + relpath)

    @property
    def body(self):
        return self.input_file.read_text()

    @property
    def description(self):
        """Returns a nice description of the post, first 2 sentences"""
        plain = self.html.strip_tags(
            remove_tags=["figcaption", "sup", "div.footnote"]
        )
        ms = re.split("(?<=\S[\.\?!])(?:\s|$)", plain, maxsplit=2, flags=re.M)

        sentences = []
        for sentence in ms[0:2]:
            sentences.extend((s.strip() for s in sentence.splitlines() if s))

        desc = " ".join(sentences)
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
        """return html of the post

        :return: str, rendered html
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
    def output_file(self):
        """this is the path of the file that this page will be outputted to
        after it is templated"""

        # see if there is a slug we should add
        input_basename = self.input_file.basename
        m = re.match(self.regex(), input_basename, flags=re.I)
        dname = m.group(1) or ""

        output_basename = self.config.page_output_basename
        return self.output_dir.child_file(dname, output_basename)

    @property
    def template_name(self):
        theme = self.config.theme
        for template_name in self.template_names:
            logger.debug("Attempting to use theme template [{}.{}]".format(
                theme.name,
                template_name
            ))
            if theme.has_template(template_name):
                return template_name

    @classproperty
    def template_names(cls):
        """this is the template that will be used to compile the post into html"""
        ret = []
        subclasses = OrderedSubclasses(Page)
        subclasses.insert(cls)
        for c in subclasses:
            if hasattr(c, "name"):
                ret.append(c.name)
        return ret

    @classmethod
    def regex(cls):
        return rf'^{cls.name}(?:[\s_-]([^\.]+))?\.(?:md|markdown)$'

    @classmethod
    def match(cls, basename):
        return bool(re.search(cls.regex(), basename, flags=re.I))

    def compile(self):
        cache = getattr(self, "_cache", ContextNamespace(cascade=False))

        context_name = self.config.context_name()
        cache.switch_context(context_name)

        if "html" not in cache:
            logger.debug("Rendering html[{}]: {}".format(context_name, self.uri))

            try:
                md = self.markdown
                html = md.output(self)
                meta = getattr(md, "Meta", {})

                title = meta.get("title", "")
                if not title:
                    m = re.match(
                        r"^\s*<h1[^>]*>([^<]*)</h1>\s*",
                        html,
                        flags=re.I | re.M
                    )
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

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        output_file = self.output_file
        logger.info("output {} [{}] to {}".format(
            self.name,
            self.title or "<NO TITLE>",
            output_file
        ))

        self.output_dir.touch()

        kwargs["prev_url"] = self.prev_url
        kwargs["prev_title"] = self.prev_title
        kwargs["next_url"] = self.next_url
        kwargs["next_title"] = self.next_title

        self.output_template(
            output_file,
            **kwargs
        )

    def output_template(self, output_file, theme=None, **kwargs):
        # not sure what name I like the best yet
        template_names = self.template_names
        template_name = self.template_name

        for tn in template_names:
            kwargs[tn] = self
        kwargs["instance"] = self

        if not theme:
            theme = self.config.theme

        logger.info(
            'Templating input file [{}] with theme.template [{}.{}] to output file [{}]'.format(
                self.input_file,
                theme.name,
                template_name,
                output_file.relative_to(self.config.output_dir)
            )
        )

        html = theme.render_template(
            template_name,
            **kwargs
        )

        for tn in template_names:
            r = event.broadcast(
                f"output.template.{tn}",
                html=HTML(html),
                **kwargs
            )

        f = Filepath(output_file, encoding=self.config.encoding)
        f.write_text(r.html)

