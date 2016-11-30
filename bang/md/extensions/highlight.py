# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re
from xml.sax.saxutils import escape

from markdown.extensions import fenced_code


class CodeBlockPreprocessor(fenced_code.FencedBlockPreprocessor):
    """Generates compatible code blocks that can be used with default highlight.js

    https://github.com/waylan/Python-Markdown/blob/master/markdown/preprocessors.py
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

                # https://wiki.python.org/moin/EscapingHtml
                block = escape(m.group('code').strip())
                code = u'<pre><code class="codeblock{}">{}</code></pre>'.format(lang, block)
                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = u'{}\n{}\n{}'.format(text[:m.start()], placeholder, text[m.end():])

            else:
                break

        return text.split("\n")


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


