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
import datetime
import os
from xml.sax.saxutils import escape
import codecs

from .. import event, echo


def get_safe(text):
    """return xml safe content with things like & < > escaped"""
    # https://wiki.python.org/moin/EscapingXml
    return escape(text)


def get_cdata(text):
    """wrap the text in cdata escaping"""
    return u'<![CDATA[{}]]>'.format(text)


def get_datestr(dt):
    """return a date from datetime like Mon, 06 Sep 2010 00:01:00 +0000"""
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


@event.bind('output.finish')
def output_rss(event_name, site):
    host = site.config.host
    if not host:
        echo.err("[WARNING] rss feed not generated because no config host set")
        return

    feedpath = os.path.join(str(site.output_dir), 'feed.rss')
    echo.out("writing feed to {}", feedpath)

    main_url = site.config.base_url
    feed_url = u'http://{}/feed.rss'.format(host)
    max_count = 10
    count = 0

    with codecs.open(feedpath, 'w+', 'utf-8') as fp:

        fp.write(u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        fp.write(u"<rss version=\"2.0\"\n")
        fp.write(u"  xmlns:atom=\"http://www.w3.org/2005/Atom\">\n")
        #fp.write(u"  xmlns:dc=\"http://purl.org/dc/elements/1.1/\"\n") # http://en.wikipedia.org/wiki/Dublin_Core
        #fp.write(u"  xmlns:dcterms=\"http://purl.org/dc/terms/\"\n")
        #fp.write(u"  xmlns:georss=\"http://www.georss.org/georss\">\n")

        fp.write(u"  <channel>\n")
        fp.write(u"    <title>{}</title>\n".format(get_safe(site.config.get('name', host))))
        fp.write(u"    <description>{}</description>\n".format(get_safe(site.config.get('description', host))))

        fp.write(u"    <link>{}</link>\n".format(get_safe(main_url)))
        fp.write(u"    <atom:link href=\"{}\" rel=\"self\"/>\n".format(get_safe(feed_url)))
        #fp.write(u"    <atom:link href=\"{}\" rel=\"alternate\"/>\n".format(main_url))

        dt = datetime.datetime.utcnow()
        fp.write(u"    <pubDate>{}</pubDate>\n".format(get_datestr(dt)))
        fp.write(u"    <lastBuildDate>{}</lastBuildDate>\n".format(get_datestr(dt)))
        fp.write(u"    <generator>github.com/Jaymon/bang</generator>\n")

        for p in reversed(site.posts):
            fp.write(u"    <item>\n")
            fp.write(u"      <title>{}</title>\n".format(get_cdata(p.title)))
            fp.write(u"      <description>{}</description>\n".format(get_cdata(p.html)))
            fp.write(u"      <link>{}</link>\n".format(get_safe(p.url)))
            fp.write(u"      <guid isPermaLink=\"false\">{}</guid>\n".format(get_safe(p.uri)))
            fp.write(u"      <pubDate>{}</pubDate>\n".format(get_datestr(p.modified)))
            fp.write(u"    </item>\n")

            count += 1
            if count >= max_count:
                break

        fp.write(u"  </channel>\n")
        fp.write(u"</rss>\n")

