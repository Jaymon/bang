# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import


from .event import event
from .types import Post
from .plugins import feed, sitemap
from .utils import PageIterator


@event("configure")
def configure(event_name, config):

    # configure feed
    config.feed_iter = PageIterator(config, [Post])
    config.sitemap_iter = PageIterator(config, [Post])


@event("output.finish")
def finish_output(event_name, config):
    # this compiles the root index.html
    p = PageIterator(config, [Post])
    for pages in p.get_pages():
        pages.output()

#     for dt_class in [Post]:
#         instances = dt_class.get_pages(config)
#         if instances:
#             output_cb = getattr(instances, "output")
#             if output_cb:
#                 output_cb()


