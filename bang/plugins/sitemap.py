"""
a plugin to generate a sitemap

http://en.wikipedia.org/wiki/Sitemaps
"""
from __future__ import absolute_import
import os
import codecs

from .. import event, echo

@event.bind('output.finish')
def output_sitemap(event_name, site):
    if not len(site.posts): return

    sitemap = os.path.join(str(site.output_dir), 'sitemap.xml')
    echo.out("writing sitemap to {}", sitemap)

    host = site.config.host
    max_count = 50000
    count = 0

    if host:
        with codecs.open(sitemap, 'w+', 'utf-8') as fp:
            fp.write(u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fp.write(u"<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n")

            for p in reversed(site.posts):
                fp.write(u"  <url>\n")
                fp.write(u"    <loc>{}</loc>\n".format(p.url))
                fp.write(u"    <lastmod>{}</lastmod>\n".format(p.modified.strftime("%Y-%m-%dT%H:%M:%S+00:00")))
                fp.write(u"    <changefreq>weekly</changefreq>\n")
                #fp.write(u'    <priority>0.8</priority>')
                fp.write(u"  </url>\n")

                count += 1
                if count >= max_count:
                    break

            fp.write(u"</urlset>\n")

    else:
        echo.err("[WARNING] sitemap not generated because no config host set")


