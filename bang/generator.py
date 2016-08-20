import os
import codecs
from distutils import dir_util
import fnmatch
import datetime
import imp
from HTMLParser import HTMLParser
import re

import markdown
from jinja2 import Environment, FileSystemLoader

from . import echo
from .md import HighlightExtension, HrefExtension, ImageExtension, \
    DomEventExtension, DelInsExtension
from . import event


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


class Config(object):
    """small wrapper around the config module that takes care of what happens if
    the config file doesn't actually exist"""
    @property
    def base_url(self):
        """Return the base url with scheme (scheme) and host and everything, if scheme
        is unknown this will use // (instead of http://) but that might make things
        like the rss feed and sitemap fail if they are used so it is recommended you
        set the scheme in your bangfile, there is a similar problem if host is empty, then
        it will just return empty string"""
        base_url = ''
        scheme = self.scheme
        if scheme:
            base_url = '{}://{}'.format(scheme, self.host)

        else:
            host = self.host
            if host:
                base_url = '//{}'.format(host)

        return base_url

    def __init__(self, project_dir):
        self.module = None
        self.fields = {
            #'scheme': 'http'
        }

        config_file = os.path.join(str(project_dir), 'bangfile.py')
        if os.path.isfile(config_file):
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            self.module = imp.load_source('bangfile_module', config_file)

        # find all environment vars
        for k, v in os.environ.iteritems():
            if k.startswith('BANG_'):
                name = k[5:].lower()
                self.fields[name] = v

    def get(self, k, default_val=None):
        """bangfile takes precedence, then environment variables"""
        ret = default_val
        if self.module:
            ret = getattr(self.module, k, self.fields.get(k, default_val))

        else:
            ret = self.fields.get(k, default_val)

        return ret

    def __getattr__(self, k):
        return self.get(k)


class Template(object):
    def __init__(self, template_dir):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        self.templates = {}
        for f in fnmatch.filter(os.listdir(str(self.template_dir)), '*.html'):
            filename, fileext = os.path.splitext(f)
            self.templates[filename] = f


    def has(self, template_name):
        return template_name in self.templates

    def output(self, template_name, filepath, **kwargs):
        tmpl = self.env.get_template("{}.html".format(template_name))
        return tmpl.stream(**kwargs).dump(filepath, encoding='utf-8')


class Posts(object):
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

    def __init__(self, output_dir, tmpl, config):
        self.output_dir = output_dir
        self.tmpl = tmpl
        self.config = config

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

    def __len__(self):
        return self.total

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        echo.out("output Posts")
        output_dir = self.output_dir
        output_dir.create()

        output_file = os.path.join(str(output_dir), self.output_basename)

        # TODO -- generate both prev and next urls if needed

        echo.out(
            'templating Posts with template "{}" to output file {}',
            self.template_name,
            output_file
        )
        self.tmpl.output(
            self.template_name,
            output_file,
            posts=self,
            config=self.config,
            **kwargs
        )

        # TODO -- after creating output_dir/index.html, then create output_dir/page/N
        # files for each page of Posts


class Post(object):
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
        v = ''
        with codecs.open(d.content_file, 'r+', 'utf-8') as fp:
            v = fp.read()
        return v

    @property
    def description(self):
        """Returns a nice description of the post, first 2 sentences"""
        desc = getattr(self, "_description", None)
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
    def html(self):
        """
        return html of the post

        base_url -- string -- if passed in, file links will be changed to base_url + post_url + filename

        return -- string -- rendered html
        """
        html = getattr(self, "_html", None)
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


    def __init__(self, directory, output_dir, tmpl, config):
        self.directory = directory
        self.output_dir = output_dir
        self.tmpl = tmpl
        self.config = config

    def normalize_markdown(self, text):
        """alternate file extension .markdown should point to .md"""
        return self.normalize_md(text)

    def normalize_md(self, text):
        """normalize markdown using the markdown module https://github.com/waylan/Python-Markdown"""
        # http://pythonhosted.org/Markdown/reference.html#markdown
        return markdown.markdown(
            text, 
            #extensions=['fenced_code', 'codehilite(guess_lang=False)', 'tables', 'footnotes', 'nl2br']
            # http://packages.python.org/Markdown/extensions/index.html
            extensions=[
                HighlightExtension(),
                'tables',
                'footnotes(UNIQUE_IDS=True)',
                'nl2br',
                'attr_list',
                'smart_strong',
                HrefExtension(self),
                ImageExtension(self),
                DomEventExtension(self),
                DelInsExtension()
            ],
            output_format="html5"
        )

    def __str__(self):
        return self.directory.path

    def output(self, **kwargs):
        """
        **kwargs -- dict -- these will be passed to the template
        """
        echo.out("output {}", self.title)
        d = self.directory
        output_dir = self.output_dir
        output_dir.create()
        for input_file in d.other_files:
            output_dir.copy_file(input_file)

        #html = self.html
        output_file = os.path.join(str(output_dir), self.output_basename)
        self.output_file = output_file

        echo.out(
            'templating {} with template "{}" to output file {}',
            d.content_file,
            self.template_name,
            output_file
        )
        self.tmpl.output(
            self.template_name,
            output_file,
            post=self,
            config=self.config,
            **kwargs
        )


class Aux(Post):
    @property
    def title(self):
        basename = os.path.basename(str(self.directory))
        return basename.capitalize()


class Site(object):
    """this is where all the magic happens. Output generates all the posts and compiles
    files from input directory to output directory"""
    def __init__(self, project_dir, output_dir):
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.config = Config(project_dir)

    def output(self):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.output_dir.clear()
        tmpl = Template(self.project_dir.template_dir)

        posts = Posts(self.output_dir, tmpl, self.config)
        auxs = Posts(self.output_dir, tmpl, self.config)

        for d in self.project_dir.input_dir:
            output_dir = self.output_dir / d.relative()
            if d.is_aux():
                echo.out("aux dir: {}", d)
                a = Aux(d, output_dir, tmpl, self.config)
                auxs.append(a)

            elif d.is_post():
                echo.out("post dir: {}", d)
                p = Post(d, output_dir, tmpl, self.config)
                posts.append(p)

            else:
                echo.out("uncategorized dir: {}", d)
                output_dir.create()
                for f in d.files():
                    output_dir.copy_file(f)

        for p in posts:
            p.output(posts=posts, auxs=auxs)

        for a in auxs:
            a.output(posts=posts, auxs=auxs)

        posts.output()

        for f in self.project_dir.input_dir.files():
            self.output_dir.copy_file(f)

        self.posts = posts
        self.auxs = auxs

        event.broadcast('output.finish', self)

