import sys
import os
import argparse
import shutil
from distutils import dir_util
import codecs
import fnmatch

import markdown
from jinja2 import Environment, FileSystemLoader

__version__ = "0.0.1"

def normalize_markdown(text):
    return markdown.markdown(text)

def normalize_html(text):
    return text


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


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    parser = argparse.ArgumentParser(description='Static site generator')
    parser.add_argument('--dir', '-d', dest='project_dir', default=os.curdir, help='directory, defaults to current working directory')
    parser.add_argument("-v", "--version", action='version', version="%(prog)s {}".format(__version__))

    ret_code = 0
    args = parser.parse_args()
    project_dir = os.path.abspath(os.path.expanduser(args.project_dir))
    srcdir = os.path.join(project_dir, "src")
    bindir = os.path.join(project_dir, "bin")
    tmpl = Template(os.path.join(project_dir, "template"))
    ext_callback = {
        'md': normalize_markdown,
        'html': normalize_html
    }

    # we are about to start all over again, so remove the bin directory
    shutil.rmtree(bindir)
    dir_util.mkpath(bindir)

    for srcroot, dirs, files in os.walk(srcdir, topdown=True):
        # ignore private dirs
        if srcdir.startswith('_'): continue

        binroot = os.path.join(bindir, srcroot.replace(srcdir, '').strip(os.sep))
        dir_util.mkpath(binroot)

        for f in files:
            # ignore private files
            if f.startswith('_'): continue

            filename, fileext = os.path.splitext(f)
            fileext = fileext.lstrip('.')
            filepath = os.path.join(srcroot, f)

            if fileext in ext_callback:
                if tmpl.has(filename):
                    with codecs.open(filepath, 'r+', 'utf-8') as fp:
                        text = fp.read()
                        html = ext_callback[fileext](text)
                        tmpl.write(
                            filename,
                            os.path.join(binroot, 'index.html'),
                            content=html,
                            title="test title"
                        )

            else:
                shutil.copy(filepath, binroot)



    return ret_code

if __name__ == u'__main__':
    sys.exit(console())

