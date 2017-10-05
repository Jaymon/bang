# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

from ... import event


class DomEventTreeprocessor(Treeprocessor):
    """support for DomEventExtension"""
    def iterparent(self, tree):
        for parent in tree.getiterator():
            for child in parent:
                yield parent, child

    def run(self, doc):
        for parent, elem in self.iterparent(doc):
            elem_event_name = 'dom.{}'.format(elem.tag)
            event.broadcast(elem_event_name, parent=parent, elem=elem, markdown=self.markdown)


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
        #def do_something(event_name, parent, elem, markdown):
            # do something cool with the "a" elem
    """
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = DomEventTreeprocessor(md)
        #self.processor.config = self.getConfigs()
        md.treeprocessors.add('domevent', self.processor, "_end")

