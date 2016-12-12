import os
import codecs
from distutils import dir_util
import fnmatch
import datetime
import imp
from HTMLParser import HTMLParser
import re
import logging

import markdown
from jinja2 import Environment, FileSystemLoader

from . import event
from . import config
from .md.extensions.delins import DelInsExtension
from .md.extensions.domevent import DomEventExtension
from .md.extensions.absolutelink import AbsoluteLinkExtension
from .md.extensions.image import ImageExtension
from .md.extensions.highlight import HighlightExtension
from .md.extensions.reference import ReferenceExtension
from .md.extensions.embed import EmbedExtension
from .path import Directory


logger = logging.getLogger(__name__)


# http://stackoverflow.com/a/925630/5006
class HTMLStripper(HTMLParser):
    """strip html tags"""
    @classmethod
    def strip_tags(cls, html):
        s = cls()
        s.feed(html)
        return s.get_data()

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class Template(object):
    """Thin wrapper around Jinja functionality that handles templating things

    http://jinja.pocoo.org/docs/dev/
    """
    def __init__(self, template_dir):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            #extensions=['jinja2.ext.with_'] # http://jinja.pocoo.org/docs/dev/templates/#with-statement
        )

        self.templates = {}
        for f in fnmatch.filter(os.listdir(str(self.template_dir)), '*.html'):
            filename, fileext = os.path.splitext(f)
            self.templates[filename] = f

    def has(self, template_name):
        return template_name in self.templates

    def output(self, template_name, filepath, **kwargs):
        tmpl = self.env.get_template("{}.html".format(template_name))
        return tmpl.stream(**kwargs).dump(filepath, encoding='utf-8')


class Posts(config.ContextAware):
    """this is a simple linked list of Post instances, the Post instances have next_post
    and prev_post pointers that this class takes advantage of to build the list"""
    first_post = None
    total = 0
    last_post = None

    template_name = 'posts'
    """this is the template that will be used to compile the posts into html"""

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

    def __init__(self, output_dir, tmpl):
        self.output_dir = output_dir
        self.tmpl = tmpl

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
            if regex and not re.search(regex, str(p.directory), re.I):
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
        self.tmpl.output(
            self.template_name,
            output_file,
            posts=self,
            config=self.config,
            **kwargs
        )

        # TODO -- after creating output_dir/index.html, then create output_dir/page/N
        # files for each page of Posts


class Post(config.ContextAware):
    """this is a node in the Posts linked list, it holds all the information needed
    to output a Post in the input directory to the output directory"""
    next_post = None
    """holds a pointer to the next Post"""

    prev_post = None
    """holds a pointer to the previous Post"""

    template_name = 'post'
    """this is the template that will be used to compile the post into html"""

    output_basename = 'index.html'
    """this is the name of the file that this post will be outputted to after it
    is templated"""

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
        d = self.directory
        t = os.path.getmtime(d.content_file)
        modified = datetime.datetime.fromtimestamp(t)
        return modified

    @property
    def uri(self):
        """the path of the post (eg, /foo/bar/post-slug)"""
        d = self.directory
        relative = d.relative()
        relative = relative.replace('\\', '/')
        v = "/".join(['', relative])
        return v

    @property
    def url(self):
        """the full url of the post with host and everything"""
        base_url = self.config.base_url
        return u"{}{}".format(base_url, self.uri)

    @property
    def title(self):
        d = self.directory
        title = os.path.splitext(os.path.basename(d.content_file))[0]
        return title

    @property
    def body(self):
        d = self.directory
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
        #html = getattr(self, "_html", None)
        html = None
        if html is None:
            d = self.directory
            ext = os.path.splitext(d.content_file)[1][1:]
            body = self.body
            ext_callback = getattr(self, "normalize_{}".format(ext), None)
            if ext_callback:
                html = ext_callback(body)
            else:
                html = body

            self._html = html

        return html


    def __init__(self, directory, output_dir, tmpl):
        self.directory = directory
        self.output_dir = output_dir
        self.tmpl = tmpl

    def normalize_markdown(self, text):
        """alternate file extension .markdown should point to .md"""
        return self.normalize_md(text)

    def normalize_md(self, text):
        """normalize markdown using the markdown module https://github.com/waylan/Python-Markdown"""
        # http://pythonhosted.org/Markdown/reference.html#markdown
        md = markdown.Markdown(
            extensions=[
                ReferenceExtension(UNIQUE_IDS=True),
                HighlightExtension(),
                'tables',
                'nl2br',
                'attr_list',
                'smart_strong',
                'meta', # http://pythonhosted.org/Markdown/extensions/meta_data.html
                'admonition', # https://pythonhosted.org/Markdown/extensions/admonition.html
                ImageExtension(),
                DelInsExtension(),
                AbsoluteLinkExtension(self),
                DomEventExtension(self),
                #"bang.md.extensions.embed(cache_dir={})".format(self.directory),
                EmbedExtension(cache_dir=self.directory),
            ],
            output_format="html5"
        )

        html = md.convert(text)
        self._meta = md.Meta
        return html

    def __str__(self):
        return self.directory.path

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        d = self.directory
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
            config=self.config,
            **kwargs
        )

#         self.tmpl.output(
#             self.template_name,
#             output_file,
#             post=self,
#             config=self.config,
#             **kwargs
#         )

    def output_template(self, template_name, output_file, **kwargs):
        kwargs["post"] = self
        self.tmpl.output(
            template_name,
            output_file,
            **kwargs
        )


class Aux(Post):

    template_name = 'aux'

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
            basename = os.path.basename(str(self.directory))
            title = basename.capitalize()

        return title

    def output_template(self, template_name, output_file, **kwargs):
        kwargs["aux"] = self
        self.tmpl.output(
            template_name,
            output_file,
            **kwargs
        )


class Other(object):
    """Holds folders that are neither Aux or Post folders"""
    next_post = None
    """never used, Posts api compatibility only"""

    prev_post = None
    """never used, Posts api compatibility only"""

    def __init__(self, directory, output_dir):
        self.directory = directory
        self.output_dir = output_dir

    def output(self):
        if self.directory.is_private(): return

        d = self.directory
        output_dir = self.output_dir

        output_dir.create()
        for f in d.files():
            output_dir.copy_file(f)


class Site(config.ContextAware):
    """this is where all the magic happens. Output generates all the posts and compiles
    files from input directory to output directory"""
    def __init__(self, project_dir, output_dir):
        self.project_dir = project_dir
        self.output_dir = output_dir

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        config.initialize(self.project_dir)

        with config.context("web"):
            if regex:
                logger.warning("output directory {} not cleared because regex present".format(self.output_dir))
            else:
                self.output_dir.clear()

            tmpl = Template(self.project_dir.template_dir)
            posts = Posts(self.output_dir, tmpl)
            auxs = Posts(self.output_dir, tmpl)
            others = Posts(self.output_dir, tmpl)

            for d in self.project_dir.input_dir:
                output_dir = self.output_dir / d.relative()
                if d.is_aux():
                    logger.debug("aux dir: {}".format(d))
                    a = Aux(d, output_dir, tmpl)
                    auxs.append(a)

                elif d.is_post():
                    logger.debug("post dir: {}".format(d))
                    p = Post(d, output_dir, tmpl)
                    posts.append(p)

                else:
                    logger.debug("other dir: {}".format(d))
                    o = Other(d, output_dir)
                    others.append(o)

            for p in posts.matching(regex):
                p.output(posts=posts, auxs=auxs)

            for a in auxs.matching(regex):
                a.output(posts=posts, auxs=auxs)

            for o in others.matching(regex):
                o.output()

            self.posts = posts
            self.auxs = auxs
            self.others = others

            if regex:
                logger.warning("Posts not compiled because regex present")
            else:
                posts.output()

                for f in self.project_dir.input_dir.files():
                    self.output_dir.copy_file(f)

            if regex:
                logger.warning("output.finish event not broadcast because regex")
            else:
                event.broadcast('output.finish', self)

