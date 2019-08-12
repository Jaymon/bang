# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from ..event import event
from ..types import TypeIterator, Page, Other
from ..path import File
from . import feed, sitemap


class Post(Page):
    """this is a node in the Posts linked list, it holds all the information needed
    to output a Post in the input directory to the output directory"""

    regex = r'\.(md|markdown)$'

    @property
    def title(self):
        title = File(self.content_file).fileroot
        return title

    @classmethod
    def match(cls, directory):
        return True if directory.files(cls.regex) else False


@event("configure.plugins")
def configure(event_name, config):
    config.feed_iter = TypeIterator(config, [Post])
    config.sitemap_iter = TypeIterator(config, [Post])

    # TODO -- there should be a better way to do this
    config.types = [Page, Post, Other]


@event("output.finish")
def compile_root_index_files(event_name, config):
    # this compiles the root index.html
    config.project.get_type(Post.name).output()
    #p = TypeIterator(config, [Post])
    #for pages in p:
    #    pages.output()

