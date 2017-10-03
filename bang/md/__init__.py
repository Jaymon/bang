# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import markdown


class Markdown(markdown.Markdown):

    def convert(self, source):

        from markdown import util

        # Fixup the source text
        if not source.strip():
            return ''  # a blank unicode string

        try:
            source = util.text_type(source)
        except UnicodeDecodeError as e:
            # Customise error message while maintaining original trackback
            e.reason += '. -- Note: Markdown only accepts unicode input!'
            raise

        # Split into lines and run the line preprocessors.
        self.lines = source.split("\n")
        #pout.v(self.lines)
        for prep in self.preprocessors.values():
            self.lines = prep.run(self.lines)

        #pout.x()
        #pout.v(self.references, self.lines)

        # Parse the high-level elements.
        root = self.parser.parseDocument(self.lines).getroot()

        #pout.v(self.serializer(root), root)

        # Run the tree-processors
        for treeprocessor in self.treeprocessors.values():
            #pout.v(treeprocessor.__class__)
            newRoot = treeprocessor.run(root)
            if newRoot is not None:
                root = newRoot

            html = self.serializer(root)
#             pout.v(html)
#             if "<a" in html:
#                 pout.x(0)


        # Serialize _properly_.  Strip top-level tags.
        output = self.serializer(root)
        if self.stripTopLevelTags:
            try:
                start = output.index(
                    '<%s>' % self.doc_tag) + len(self.doc_tag) + 2
                end = output.rindex('</%s>' % self.doc_tag)
                output = output[start:end].strip()
            except ValueError:  # pragma: no cover
                if output.strip().endswith('<%s />' % self.doc_tag):
                    # We have an empty document
                    output = ''
                else:
                    # We have a serious problem
                    raise ValueError('Markdown failed to strip top-level '
                                     'tags. Document=%r' % output.strip())

        # Run the text post-processors
        for pp in self.postprocessors.values():
            output = pp.run(output)

        return output.strip()
