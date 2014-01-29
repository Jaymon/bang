"""in this module, we fix all the problems with markdown's default code display stuff"""
import re

from markdown.extensions import codehilite, fenced_code
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter


class HighlightExtension(fenced_code.FencedCodeExtension):
    """
    A compatible extenstion to highlight.js for python-markdown

    http://highlightjs.org
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

