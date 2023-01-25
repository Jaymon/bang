# -*- coding: utf-8 -*-

from bang import event


# uncomment the plugins you want your project to use
# from bang.plugins import (
#     blog, # is this website a blog?
#     favicon, # autodiscover favicons
#     amp, # support Google's amp
#     sitemap, # enable sitemap support
#     feed, # enable rss feed support
#     googleanalytics, # enable Google Analytics
#     opengraph, # enable open graph support
#     breadcrumbs, # put subfolder navigation in each folder
# )


# main configuration for your project
@event("configure.project")
def configure_project(event, config):
    config.load_environ()

    config.scheme = "http"
    if config.env == "prod":
        config.scheme = "https"


# any theme specific configuration can go here
@event("configure.theme")
def configure_plugins(event, config):
    pass


# handle output context exclusive configuration
@event('context.output')
def context_output(event_name, config):
    # for support of both https and http on html pages, this results in //host/path/ urls
    config.scheme = ""


