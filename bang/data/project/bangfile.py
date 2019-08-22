# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

from bang import event

# uncomment if you would like this website to be a blog
# from bang.plugins import blog

# uncomment if you would like to support amp pages
# from bang.plugins import amp


# main configuration for your project
@event("configure.project")
def configure_plugins(event, config):
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
def context_web(event_name, config):
    # for support of both https and http on html pages, this results in //host/path/ urls
    config.scheme = ""


