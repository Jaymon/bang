# -*- coding: utf-8 -*-
"""
Why do I render the feed myself? Because every library I found needed too many other
dependencies and some were a real pain to install (you need lxml? Seriously?). So
I just render the feed raw

http://en.wikipedia.org/wiki/RSS
https://github.com/lkiesow/python-feedgen
http://cyber.law.harvard.edu/rss/rss.html

validator: http://validator.w3.org/feed/
big list of namespaces: http://validator.w3.org/feed/docs/howto/declare_namespaces.html
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import datetime
import os
from xml.sax.saxutils import escape
import codecs
import logging

from ..event import event


logger = logging.getLogger(__name__)


def get_safe(text):
    """return xml safe content with things like & < > escaped"""
    # https://wiki.python.org/moin/EscapingXml
    return escape(text)


def get_cdata(text):
    """wrap the text in cdata escaping"""
    return '<![CDATA[{}]]>'.format(text)


def get_datestr(dt):
    """return a date from datetime like Mon, 06 Sep 2010 00:01:00 +0000"""
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


@event('output.finish')
def output_rss(event_name, site):
    with site.config.context("feed") as conf:
        feed_enabled = conf.get("feed_enabled", True)
        if not feed_enabled: return

        host = conf.host
        if not host:
            logger.error("RSS feed not generated because no config host set")
            return

        feedpath = os.path.join(str(site.output_dir), 'feed.rss')
        logger.info("writing feed to {}".format(feedpath))

        main_url = conf.base_url
        feed_url = 'http://{}/feed.rss'.format(host)
        max_count = conf.get("feed_max_count", 10)
        count = 0

        with codecs.open(feedpath, 'w+', 'utf-8') as fp:

            fp.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fp.write("<rss version=\"2.0\"\n")
            fp.write("  xmlns:atom=\"http://www.w3.org/2005/Atom\">\n")
            #fp.write("  xmlns:dc=\"http://purl.org/dc/elements/1.1/\"\n") # http://en.wikipedia.org/wiki/Dublin_Core
            #fp.write("  xmlns:dcterms=\"http://purl.org/dc/terms/\"\n")
            #fp.write("  xmlns:georss=\"http://www.georss.org/georss\">\n")

            fp.write("  <channel>\n")
            fp.write("    <title>{}</title>\n".format(get_safe(conf.get('name', host))))
            fp.write("    <description>{}</description>\n".format(get_safe(conf.get('description', host))))

            fp.write("    <link>{}</link>\n".format(get_safe(main_url)))
            fp.write("    <atom:link href=\"{}\" rel=\"self\"/>\n".format(get_safe(feed_url)))
            #fp.write(u"    <atom:link href=\"{}\" rel=\"alternate\"/>\n".format(main_url))

            dt = datetime.datetime.utcnow()
            fp.write("    <pubDate>{}</pubDate>\n".format(get_datestr(dt)))
            fp.write("    <lastBuildDate>{}</lastBuildDate>\n".format(get_datestr(dt)))
            fp.write("    <generator>github.com/Jaymon/bang</generator>\n")

            for p in conf.feed_iter(site):
                fp.write("    <item>\n")
                fp.write("      <title>{}</title>\n".format(get_cdata(p.title)))
                fp.write("      <description>{}</description>\n".format(get_cdata(p.html)))
                fp.write("      <link>{}</link>\n".format(get_safe(p.url)))
                fp.write("      <guid isPermaLink=\"false\">{}</guid>\n".format(get_safe(p.uri)))
                fp.write("      <pubDate>{}</pubDate>\n".format(get_datestr(p.modified)))
                fp.write("    </item>\n")

                count += 1
                if count >= max_count:
                    break

            fp.write("  </channel>\n")
            fp.write("</rss>\n")

