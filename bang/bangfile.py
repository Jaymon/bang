# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from .event import event
from .types import Page, TypeIterator
from .plugins import sitemap


@event("configure")
def configure(event_name, config):
    config.sitemap_iter = TypeIterator(config, [Page])


