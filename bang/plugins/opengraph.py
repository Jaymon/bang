# -*- coding: utf-8 -*-
"""
Open Graph

http://ogp.me/
"""

from ..compat import *
from ..event import event


@event("output.template.page")
def template_output_ga(event):

    instance = event.instance

    s = [
        '<meta name="description" content="{}">'.format(instance.description),
        '<meta property="og:url" content="{}">'.format(instance.url),
        '<meta property="og:type" content="article">',
        '<meta property="og:title" content="{}">'.format(instance.title),
        '<meta property="og:description" content="{}">'.format(instance.description),
        '<meta property="og:image" content="{}">'.format(instance.image),
    ]

    event.html = event.html.inject_into_head("\n".join(s))

