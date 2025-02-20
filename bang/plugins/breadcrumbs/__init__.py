# -*- coding: utf-8 -*-
"""
Breadcrumbs plugin

This will generate a page with a list of all the pages in a folder that doesn't
already have an index.html file, this is really handy if you want to have multiple
levels of navigation.

This plugin will check your current theme for a `breadcrumbs.html` template file,
otherwise it will fallback to its default template.
"""
import logging
from collections import defaultdict

from ...compat import *
from ...event import event
from ...types import PageIterator
from ...path import DataDirpath


logger = logging.getLogger(__name__)


@event("configure.plugins")
def configure_plugins_breadcrumbs(event):
    config = event.config
    config.setdefault("breadcrumbs_iter", PageIterator(config))


@event('configure.theme')
def configure_context_breadcrumbs(event):
    # we do this here so the project has a chance to set a theme
    config = event.config
    theme = config.theme
    if not theme.has_template("breadcrumbs"):
        dd = DataDirpath(__name__)
        theme.template_dirs.append(dd.child_dir("template"))


@event('output.finish')
def output_breadcrumbs(event):
    config = event.config

    with config.context("breadcrumbs") as config:

        d = defaultdict(list)
        for p in config.breadcrumbs_iter:
            for bc in p.url.paths:
                d[bc].append(p)

        theme = config.theme
        basename = config.page_output_basename

        for breadcrumb, instances in d.items():
            path = config.output_dir.child_dir(breadcrumb)

            # we only want to add breadcrumb files to directories that don't
            # have any index files already
            if not path.has_file(basename):
                logger.debug("Generating breadcrumb for {}".format(breadcrumb))
                theme.output_template(
                    "breadcrumbs",
                    path.child_file(basename),
                    breadcrumb=breadcrumb,
                    path=path,
                    instances=instances,
                )

