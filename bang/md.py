"""
in this module, we fix all the problems with markdown's default code display stuff

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

http://pythonhosted.org/Markdown/extensions/api.html

https://github.com/waylan/Python-Markdown/wiki/Third-Party-Extensions
"""
import re
import os

from markdown.extensions import codehilite, fenced_code
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from . import event

class DomEventTreeprocessor(Treeprocessor):
    """support for HrefExtension"""
    def iterparent(self, tree):
        for parent in tree.getiterator():
            for child in parent:
                yield parent, child

    def run(self, doc):
        post = self.config['post']
        for parent, elem in self.iterparent(doc):
            elem_event_name = 'dom.{}'.format(elem.tag)
            event.broadcast(elem_event_name, parent=parent, elem=elem, **self.config)


class DomEventExtension(Extension):
    """
    this will modify all a href attributes to be full url paths

    if it is an http://... url, nothing happens, if it is a path.ext then it
    will be converted to a full url (http://domain.com/relative/path.ext), and if
    it is a /full/path then it will be converted to http://domain.com/full/path

    based off of:
    https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/headerid.py
    """
    def __init__(self, post):
        self.config = {
            'post' : [post, 'the post instance this extension is working on'],
        }

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = HrefTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
        #md.treeprocessors.add('href', self.processor, ">")
        md.treeprocessors['domevent'] = self.processor


class HrefTreeprocessor(Treeprocessor):
    """
    support for HrefExtension

    http://effbot.org/zone/pythondoc-elementtree-ElementTree.htm
    """
    URL_RE = re.compile(ur"^(?:https?:\/\/|\/\/)", re.I)

    def normalize_url(self, url):
        """normalizes the url into a full url"""
        m = self.URL_RE.search(url)
        if not m:
            post = self.config['post']
            config = post.config
            uri = post.uri
            base_url = config.base_url

            if url.startswith('/'):
                url = "{}{}".format(base_url, url)

            else:
                for f in post.directory.other_files:
                    basename = os.path.basename(f)
                    if url == basename:
                        url = "{}/{}".format(post.url, basename)

        return url

    def run(self, doc):
        for elem in doc.getiterator():
            if elem.tag == 'a':
                href = elem.get('href')
                url = self.normalize_url(href)
                elem.set('href', url)


class HrefExtension(Extension):
    """
    this will modify all a href attributes to be full url paths

    if it is an http://... url, nothing happens, if it is a path.ext then it
    will be converted to a full url (http://domain.com/relative/path.ext), and if
    it is a /full/path then it will be converted to http://domain.com/full/path

    based off of:
    https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/headerid.py
    """
    def __init__(self, post):
        self.config = {
            'post' : [post, 'the post instance this extension is working on'],
        }

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = HrefTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
        #md.treeprocessors.add('href', self.processor, ">")
        md.treeprocessors['href'] = self.processor


class ImageTreeprocessor(HrefTreeprocessor):
    """support for ImageExtension"""
    def iterparent(self, tree):
        """
        http://effbot.org/zone/element.htm
        """
        for parent in tree.getiterator():
            for child in parent:
                yield parent, child

    def run(self, doc):
        post = self.config['post']
        config = post.config
        for parent_elem, elem in self.iterparent(doc):
            if elem.tag == 'img':
                class_attr = parent_elem.get('class')
                if not class_attr: class_attr = ''
                img_class = ''
                if len(parent_elem) == 1:
                    head_text = parent_elem.text
                    if not head_text: head_text = ''
                    head_text = head_text.strip()

                    tail_text = elem.tail
                    if not tail_text: tail_text = ''
                    tail_text = tail_text.strip()

                    if head_text or tail_text:
                        img_class += ' image-floating'

                    else:
                        img_class += ' image-centered'

                else:
                    img_class += ' image-floating'

                class_attr += img_class
                parent_elem.set('class', class_attr.strip())

                # also normalize the url
                src = elem.get('src')
                url = self.normalize_url(src)
                elem.set('src', url)


class ImageExtension(Extension):
    """
    this looks at img tags and makes sure they are centered if they are solo or floating
    if they are in paragraph's with content
    """
    def __init__(self, post):
        self.config = {
            'post' : [post, 'the post instance this extension is working on'],
        }

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = ImageTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
        #md.treeprocessors.add('href', self.processor, ">")
        md.treeprocessors['image'] = self.processor


class HighlightExtension(fenced_code.FencedCodeExtension):
    """
    A compatible extenstion to highlight.js for python-markdown

    http://highlightjs.org
    https://github.com/isagalaev/highlight.js

    extends this markdown ext: http://pythonhosted.org/Markdown/extensions/fenced_code_blocks.html
    """
    def extendMarkdown(self, md, md_globals):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.add(
            'code_block',
            CodeBlockPreprocessor(md),
            ">normalize_whitespace"
        )


class CodeBlockFormatter(HtmlFormatter):
    """
    based off the example found here: http://pygments.org/docs/formatters/

    http://pygments.org/docs/
    """
    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, source):
        code_tag = '<code>'
        if self.cssclass:
            code_tag = '<code class="{}">'.format(self.cssclass)

        yield 0, '<pre>{}'.format(code_tag)
        for i, t in source:
            yield i, t
        yield 0, '</code></pre>'


class CodeBlockPreprocessor(fenced_code.FencedBlockPreprocessor):
    """
    Generates compatible code blocks that can be used with default highlight.js
    """
    FENCED_BLOCK_RE = re.compile(
        ur"^(?P<fence>(?:`{3,}))[ ]*(?P<lang>[a-z0-9_+-]*)[ ]*(?P<code>.*?)(?<=\n)(?P=fence)[ ]*$",
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

    def run(self, lines):
        """ Match and store Fenced Code Blocks in the HtmlStash. """
        text = u"\n".join(lines)
        while 1:
            m = self.FENCED_BLOCK_RE.search(text)
            if m:
                lang = 'no-highlight'
                if m.group('lang'):
                    lang = m.group('lang')

                try:
                    lexer = get_lexer_by_name(lang)

                except ValueError:
                    lexer = TextLexer()

                formatter = CodeBlockFormatter(cssclass="codeblock {}".format(lang))
                code = highlight(m.group('code'), lexer, formatter)

                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = u'{}\n{}\n{}'.format(text[:m.start()], placeholder, text[m.end():])

            else:
                break

        return text.split("\n")

