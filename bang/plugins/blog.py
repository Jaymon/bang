# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from ..event import event
from ..types import TypeIterator, Page
from . import feed, sitemap, opengraph


class Post(Page):
    """this is a node in the Posts linked list, it holds all the information needed
    to output a Post in the input directory to the output directory"""
    def find_title(self, html):
        raise ValueError(f"Blog Posts should have a title, please add one or convert to {super().name}")


@event("configure.plugins")
def configure_blog(event, config):
    config.feed_iter = TypeIterator(config, [Post]).reverse()
    config.add_type(Post)


@event("output.html.finish")
def compile_root_index_files(event, config):
    # this compiles the root index.html
    config.project.get_type(Post.name).output()

