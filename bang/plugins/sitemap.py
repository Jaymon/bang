# -*- coding: utf-8 -*-
"""
a plugin to generate a sitemap

http://en.wikipedia.org/wiki/Sitemaps
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import codecs
import logging

from ..compat import *
from ..event import event


logger = logging.getLogger(__name__)


@event('output.finish')
def output_sitemap(event_name, config):
    if not config.sitemap_iter.has(): return

    with config.context("sitemap") as config:
        enabled = config.get("sitemap_enabled", True)
        if not enabled: return

        sitemap = os.path.join(String(config.output_dir), 'sitemap.xml')
        logger.info("writing sitemap to {}".format(sitemap))

        host = config.host
        max_count = config.get("sitemap_max_count", 50000)
        count = 0

        if host:
            with codecs.open(sitemap, 'w+', 'utf-8') as fp:
                fp.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
                fp.write("<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n")

                for p in config.sitemap_iter:
                    fp.write("  <url>\n")
                    fp.write("    <loc>{}</loc>\n".format(p.url))
                    fp.write("    <lastmod>{}</lastmod>\n".format(p.modified.strftime("%Y-%m-%dT%H:%M:%S+00:00")))
                    fp.write("    <changefreq>weekly</changefreq>\n")
                    #fp.write(u'    <priority>0.8</priority>')
                    fp.write("  </url>\n")

                    count += 1
                    if count >= max_count:
                        break

                fp.write("</urlset>\n")

        else:
            logger.error("Sitemap not generated because no config host set")

