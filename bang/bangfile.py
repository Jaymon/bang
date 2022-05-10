# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from .event import event
from .types import Page, TypeIterator
from .plugins import sitemap, favicon


# handle html context exclusive configuration
@event('context.html')
def context_html(event, config):
    # support both https and http on html pages, results in //host/path/ urls
    config.scheme = ""

