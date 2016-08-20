"""
takes the last post and makes a root index file with that post's contentb

8-18-2016 - This is DEPRECATED in favor of the built-in posts generator now, but I'm leaving
it here for a bit as an example of how to use the events system before I get rid of it

"""
from __future__ import absolute_import
import os
import codecs

from .. import event, echo

@event.bind('output.finish')
def output_index(event_name, site):
    if not len(site.posts):
        echo.err("[WARNING] cannot created index.html file because there are no posts")
        return

    # the root index will point to the last post
    p = site.posts.last_post
    if p:
        if site.output_dir.has_index():
            echo.err("[WARNING] not creating index.html file of last post because index file already exists")

        else:
            site.output_dir.copy_file(p.output_file)


