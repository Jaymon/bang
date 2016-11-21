"""
in this module, we fix all the problems with markdown's default code display stuff

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

http://pythonhosted.org/Markdown/extensions/api.html

https://github.com/waylan/Python-Markdown/wiki/Third-Party-Extensions
"""
import re
import os

from markdown.extensions import codehilite, fenced_code, Extension
from markdown.inlinepatterns import SimpleTagPattern

from markdown.extensions.footnotes import FootnoteExtension as BaseFootnoteExtension, \
    FootnotePattern as BaseFootnotePattern

from markdown.inlinepatterns import ImagePattern as BaseImagePattern, \
    ImageReferencePattern as BaseImageReferencePattern

from markdown.treeprocessors import Treeprocessor
from . import event


class DelInsExtension(Extension):
    """
    Adds delete/insert support

    I cribbed this from https://github.com/aleray/mdx_del_ins/blob/master/mdx_del_ins.py
    """
    DEL_RE = r"(\~{2})(.+?)(\~{2})"
    INS_RE = r"(\+{2})(.+?)(\+{2})"

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('del', SimpleTagPattern(self.DEL_RE, 'del'), '<not_strong')
        md.inlinePatterns.add('ins', SimpleTagPattern(self.INS_RE, 'ins'), '<not_strong')


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
            event.broadcast(elem_event_name, parent=parent, elem=elem, config=self.config)


class DomEventExtension(Extension):
    """
    This will broadcast an event for every dom element found while a post is converted
    from Markdown to HTML

    to take advantage of this extension you would subscribe to:

        dom.ELEMENT

    so, if you wanted to manipulate all a tags, you would subscribe to:

        dom.a

    example --
        @event.bind('dom.a')
        #def do_something(event_name, parent, elem, config):
            # do something cool with the "a" elem
    """
    def __init__(self, post):
        self.config = {
            'post' : [post, 'the post instance this extension is working on'],
        }

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = DomEventTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
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
                url = "{}/{}".format(post.url, url)
#                 for f in post.directory.other_files:
#                     basename = os.path.basename(f)
#                     pout.v(basename, url)
#                     if url == basename:
#                         url = "{}/{}".format(post.url, basename)

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

    def normalize_str(self, text):
        if not text: text = ''
        text = text.strip()
        return text

    def run(self, doc):
        post = self.config['post']
        config = post.config
        for child in doc.getiterator():
            if child.tag == 'p':
                has_image = False
                text = self.normalize_str(child.text)
                for grandchild in child.getiterator():
                    if grandchild.tag == 'img':
                        text += self.normalize_str(grandchild.tail)
                        # also normalize the url
                        src = grandchild.get('src')
                        url = self.normalize_url(src)
                        grandchild.set('src', url)
                        has_image = True

                if has_image:
                    class_attr = self.normalize_str(child.get('class'))
                    class_attr = ' image-floating' if text else ' image-centered'
                    child.set('class', class_attr.strip())


class ImagePattern(BaseImagePattern):
    """over-rides parent to swap alt with title if title is empty and then use
    the basename of src as the alt"""
    def handleMatch(self, m):
        el = super(ImagePattern, self).handleMatch(m)
        if el is not None:
            title = el.get("title")
            if not title:
                alt = el.get("alt")
                el.set("title", alt)
                src = el.get("src")
                el.set("alt", os.path.basename(src))

        return el


class ImageReferencePattern(BaseImageReferencePattern):
    """over-rides parent to swap alt with title if title is empty and then use
    the basename of src as the alt"""
    def makeTag(self, href, title, text):
        if not title:
            title = text
            text = os.path.basename(href)
        return super(ImageReferencePattern, self).makeTag(href, title, text)


class ImageExtension(Extension):
    """
    this looks at img tags and makes sure they are centered if they are solo or floating
    if they are in paragraph's with content, this also loosens markdown parsing so
    something like:

        ![title text](name.jpg)

    will set "title text" to the title attribute instead of the alt attribute, the
    alt tag will be set with the basename of the image, this just makes the markdown
    syntax have a bit less cognitive overhead, if you specify a title it will use
    that instead, so ![alt](name.jpg "title text") would still work
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

        md.inlinePatterns["image_link"] = ImagePattern(
            md.inlinePatterns["image_link"].pattern,
            md
        )
        md.inlinePatterns["image_reference"] = ImageReferencePattern(
            md.inlinePatterns["image_reference"].pattern,
            md
        )


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
        while True:
            m = self.FENCED_BLOCK_RE.search(text)
            if m:
                lang = u' no-highlight'
                if m.group('lang'):
                    lang = u' ' + m.group('lang')

                code = u'<pre><code class="codeblock{}">{}</code></pre>'.format(lang, m.group('code').strip())
                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = u'{}\n{}\n{}'.format(text[:m.start()], placeholder, text[m.end():])

            else:
                break

        return text.split("\n")


class FootnoteExtension(BaseFootnoteExtension):
    """
    This extends the included footnote extension and allows an easy footnote where
    you can just use [^n] for each of the footnotes and if you just make sure your
    definitions are in order then everything will work. While this isn't compatible with
    other markdown it makes it easier for me to write posts, and I'm all about
    removing friction in blog posts

    https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/footnotes.py
    """
    def __init__(self, *args, **kwargs):
        super(FootnoteExtension, self).__init__(*args, **kwargs)
        self.config.setdefault(
            "EASY_PLACEHOLDER",
            ["n", "the text string that marks autoincrement footers"]
        )

    def extendMarkdown(self, md, md_globals):
        """ Add pieces to Markdown. """
        super(FootnoteExtension, self).extendMarkdown(md, md_globals)

        # what we do here is we allow the parent to configure everything and then
        # we just go in and replace the pattern matcher with our own, silently, like a ninja
        md.inlinePatterns["footnote"] = FootnotePattern(md.inlinePatterns["footnote"].pattern, self)

    def reset(self):
        super(FootnoteExtension, self).reset()
        self.found_id = 1
        self.matched_id = 1

    def setFootnote(self, id, text):
        """This differs from parent by using our own id if passed in id matches
        our placeholder, otherwise it is transparent"""
        found_id = id
        placeholder = self.getConfig("EASY_PLACEHOLDER")
        if id == placeholder:
            found_id = self.found_id
            self.found_id += 1

        return super(FootnoteExtension, self).setFootnote(found_id, text)


class FootnotePattern(BaseFootnotePattern):
    def handleMatch(self, m):
        """This differs from parent by just incrementing footnotes.match_id if the
        placeholder was used, otherwise is is transparent
        """
        id = m.group(2)
        m_id = m

        placeholder = self.footnotes.getConfig("EASY_PLACEHOLDER")
        if id == placeholder:
            class MatchId(object):
                def __init__(self, id):
                    self.id = id
                def group(self, *args):
                    return self.id

            m_id = MatchId(self.footnotes.matched_id)
            self.footnotes.matched_id += 1

        return super(FootnotePattern, self).handleMatch(m_id)


class PlaceholderDict(dict):
    """Small wrapper around a dict that monitors set/get/contains for a placeholder
    key and if it sees it then it will change that key to an auto-increment key
    and return the matching internal key, basically, it allows you to do something
    like:
        d = PlaceholderDict("foo")
        d["foo"] = 1
        d["foo"] = 2

    and save both 1 and 2 in the dict. It only works for setitem/getitem/contains though, 
    so you can't do d.get("foo") and have it work

    NOTE -- for when I try to make FootnoteExtension use this again, you would need
        this to extend orderedDict, and also you would need an placeholder_index_i
        instance variable, and you would need to handle .keys() and .index() calls
        successfully, then I think it would work (see the original FootnotePattern
        for where these are used)
    """
    def __init__(self, placeholder, *args, **kwargs):
        super(PlaceholderDict, self).__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_set_i = 1
        self.placeholder_get_i = 1

    def get_key(self, k, placeholder_i):
        if k == self.placeholder:
            k = "{}-{}".format(self.placeholder, placeholder_i)
        return k

    def __setitem__(self, k, v):
        nk = self.get_key(k, self.placeholder_set_i)
        self.placeholder_set_i += 1
        super(PlaceholderDict, self).__setitem__(nk, v)

    def __getitem__(self, k):
        nk = self.get_key(k, self.placeholder_get_i)
        self.placeholder_get_i += 1
        return super(PlaceholderDict, self).__getitem__(nk)

    def __contains__(self, k):
        nk = self.get_key(k, self.placeholder_get_i)
        return super(PlaceholderDict, self).__contains__(nk)


class ReferenceExtension(Extension):
    """Similar to the FootnoteExtension, this allows all reference links to just be
    a placeholder (eg, [n]) and as long as they are in order the correct link will
    be associated with the correct a tag"""
    def __init__(self, *args, **kwargs):
        self.config = {
            "EASY_PLACEHOLDER": ["n", "the text string that marks autoincrement references"],
        }
        super(ReferenceExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        # we just replace the standard references dict with our implementation
        # and then let the builtin plugins do all the heavy lifting
        md.references = PlaceholderDict(self.getConfig("EASY_PLACE_MARKER"))



# from markdown.inlinepatterns import ImagePattern as BaseImagePattern
# 
# class ImagePattern(BaseImagePattern):
#     def handleMatch(self, m):
#         el = super(ImagePattern, self).handleMatch(m)
#         if el:
#             pout.v(el)
#         return el
# 
# 
# class ImgExtension(Extension):
#     def extendMarkdown(self, md, md_globals):
#         # we just replace the standard references dict with our implementation
#         # and then let the builtin plugins do all the heavy lifting
#         md.inlinePatterns["image_link"] = ImagePattern(md.inlinePatterns["image_link"].pattern, md)
# 
