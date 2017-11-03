# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import


from .event import event
from .types import Post
from .plugins import feed, sitemap


@event("config")
def configure(event_name, conf):

    # configure feed
    def post_iter(site):
        #for dt_class in conf.dirtypes:
        for dt_class in [Post]:
            instances = getattr(site, dt_class.list_name)
            for instance in reversed(instances):
                yield instance

    conf.feed_iter = post_iter
    conf.sitemap_iter = post_iter


@event("output.finish")
def finish_output(event_name, site):
    # this compiles the root index.html
    for dt_class in [Post]:
        instances = getattr(site, dt_class.list_name)
        if instances:
            output_cb = getattr(instances, "output")
            if output_cb:
                output_cb()


