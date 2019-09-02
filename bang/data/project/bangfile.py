# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

from bang import event


# uncomment the plugins you want your project to use
# from bang.plugins import (
#     blog, # is this website a blog?
#     favicon, # autodiscover favicons
#     amp, # support Google's amp
#     sitemap, # enable sitemap support
#     feed, # enable rss feed support
#     googleanalytics, # enable Google Analytics
#     opengraph # enable open graph support
# )


# main configuration for your project
@event("configure.project")
def configure_project(event, config):
    config.env = os.environ.get("BANG_ENV", "dev")
    config.host = os.environ.get("BANG_HOST", "")
    #config.name = "PROJECT NAME"

    config.scheme = "http"
    if config.env == "prod":
        config.scheme = "https"


# any theme specific configuration can go here
@event("configure.theme")
def configure_plugins(event, config):
    pass


# handle html context exclusive configuration
@event('context.html')
def context_html(event_name, config):
    # for support of both https and http on html pages, this results in //host/path/ urls
    config.scheme = ""


