import os
import codecs
from distutils import dir_util
import fnmatch
import datetime
import imp

import markdown
from jinja2 import Environment, FileSystemLoader

from . import echo
from .md import HighlightExtension
from . import event


class Config(object):
    """small wrapper around the config module that takes care of what happens if
    the config file doesn't actually exist"""
    def __init__(self, project_dir):
        self.module = None

        config_file = os.path.join(str(project_dir), 'config.py')
        if os.path.isfile(config_file):
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            self.module = imp.load_source('config_module', config_file)

    def get(self, k, default_val=None):
        ret = default_val
        if self.module:
            ret = getattr(self.module, k, default_val)

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
    """this is a simple linked list"""
    first_post = None
    total = 0
    last_post = None

    def append(self, post):
        if not self.first_post:
            self.first_post = post

        if self.last_post:
            post.prev_post = self.last_post
            self.last_post.next_post = post

        self.last_post = post
        self.total += 1

    def count(self): return self.total

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

    def __len__(self):
        return self.total


class Post(object):
    """this is a node to the Posts linked list"""
    next_post = None
    prev_post = None
    template_name = 'index'
    output_basename = 'index.html'

    @property
    def modified(self):
        d = self.directory
        t = os.path.getmtime(d.content_file)
        modified = datetime.datetime.fromtimestamp(t)
        return modified

    @property
    def url(self):
        d = self.directory
        relative = d.relative()
        relative = relative.replace('\\', '/')
        v = "/".join(['', relative])
        return v

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
    def html(self):
        d = self.directory
        ext = os.path.splitext(d.content_file)[1][1:]
        body = self.body
        permalink = self.url
        for input_file in d.other_files:
            basename = os.path.basename(input_file)
            file_permalink = "{}/{}".format(permalink, basename)
            body = body.replace(basename, file_permalink)

        ext_callback = getattr(self, "normalize_{}".format(ext), None)
        if ext_callback:
            html = ext_callback(body)
        else:
            html = body

        return html

    def __init__(self, directory, output_dir, tmpl):
        self.directory = directory
        self.output_dir = output_dir
        self.tmpl = tmpl

    def normalize_markdown(self, text):
        """alternate file extension .markdown should point to .md"""
        return self.normalize_md(text)

    def normalize_md(self, text):
        # http://packages.python.org/Markdown/extensions/index.html
        return markdown.markdown(
            text, 
            #extensions=['fenced_code', 'codehilite(guess_lang=False)', 'tables', 'footnotes', 'nl2br']
            extensions=[HighlightExtension(), 'tables', 'footnotes', 'nl2br']
        )

    def __str__(self):
        return self.directory.path

    def output(self):
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
            post=self
        )


class Aux(Post):
    @property
    def title(self):
        basename = os.path.basename(str(self.directory))
        return basename.capitalize()


class Site(object):
    """this is where all the magic happens. Output generates all the posts and compiles
    files from input to output dirs"""
    def __init__(self, project_dir, output_dir):
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.config = Config(project_dir)

    def output(self):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.output_dir.clear()
        tmpl = Template(self.project_dir.template_dir)
        posts = Posts()
        auxs = Posts()
        for d in self.project_dir.input_dir:
            output_dir = self.output_dir / d.relative()
            if d.is_aux():
                echo.out("aux dir: {}", d)
                a = Aux(d, output_dir, tmpl)
                auxs.append(a)

            elif d.is_post():
                echo.out("post dir: {}", d)
                p = Post(d, output_dir, tmpl)
                posts.append(p)

            else:
                echo.out("uncategorized dir: {}", d)
                output_dir.create()
                for f in d.files():
                    output_dir.copy_file(f)

        for p in posts:
            p.output()

        for a in auxs:
            a.output()

        for f in self.project_dir.input_dir.files():
            self.output_dir.copy_file(f)

        # the root index will point to the last post
        p = posts.last_post
        if p:
            self.output_dir.copy_file(p.output_file)

        self.posts = posts
        self.auxs = auxs

        event.broadcast('output.finish', self)

