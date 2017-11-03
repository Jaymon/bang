# -*- coding: utf-8 -*-
"""
a plugin to generate a sitemap

http://en.wikipedia.org/wiki/Sitemaps
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import codecs
import logging

from ..event import event


logger = logging.getLogger(__name__)


@event('output.finish')
def output_sitemap(event_name, site):
    if not len(site.posts): return

    with site.config.context("sitemap") as conf:
        enabled = conf.get("sitemap_enabled", True)
        if not enabled: return

        sitemap = os.path.join(str(site.output_dir), 'sitemap.xml')
        logger.info("writing sitemap to {}".format(sitemap))

        host = conf.host
        max_count = conf.get("sitemap_max_count", 50000)
        count = 0

        if host:
            with codecs.open(sitemap, 'w+', 'utf-8') as fp:
                fp.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
                fp.write("<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n")

                for p in conf.sitemap_iter(site):
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

