# -*- coding: utf-8 -*-
"""
Turn your site into a blog by importing this plugin

This adds a Post type (post.md) that will be considered a blog post. It also
switches iteration so only post.md files will be considered for things like the
rss feed 
"""

from ..event import event
from ..types import TypeIterator, Page
from . import feed, sitemap, opengraph


class Post(Page):
    """this is a node in the Posts linked list, it holds all the information
    needed to output a Post in the input directory to the output directory"""
    def find_title(self, html):
        raise ValueError(
            "Blog Posts should have a title, please add one or convert to page.md"
        )


@event("configure.plugins")
def configure_blog(event, config):
    config.feed_iter = TypeIterator(config, [Post]).reverse()
    config.add_type(Post)


@event("output.finish.post")
def compile_root_index_files(event, config):
    # this compiles the root index.html
    config.project.get_types(Post.name).output()

