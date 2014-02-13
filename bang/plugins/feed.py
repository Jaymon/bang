# https://github.com/lkiesow/python-feedgen
import datetime
import os

from feedgen.feed import FeedGenerator

from .. import event, echo

def output_rss(event_name, site):
    host = site.config.host
    if not host:
        echo.err("[WARNING] rss feed not generated because no config host set")
        return

    fg = FeedGenerator()

    #fg.id('http://lernfunk.de/media/654321')
    fg.title(site.config.get('name', host))
    fg.description(site.config.get('description', host))
    name = site.config.name
    if name:
        fg.author(name=name)

    fg.link(href='http://{}'.format(host), rel='alternate')
    #fg.logo('http://ex.com/logo.jpg')
    #fg.subtitle('This is a cool feed!')
    fg.link(href='http://{}/feed.rss'.format(host), rel='self')
    #fg.language('en')
    fg.pubDate(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
 
    max_count = 10
    count = 0

    for p in reversed(site.posts):
        uri = p.url
        fe = fg.add_entry()
        fe.id(uri)
        fe.title(p.title)
        fe.link(href=u'http://{}{}'.format(host, uri))
        fe.description(p.html)
        fe.published(p.modified.strftime("%Y-%m-%dT%H:%M:%SZ"))

        count += 1
        if count >= max_count:
            break

    fg.rss_file(os.path.join(str(site.output_dir), 'feed.rss'))

event.listen('output.finish', output_rss)

