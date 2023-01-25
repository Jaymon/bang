# -*- coding: utf-8 -*-
"""
Breadcrumbs plugin

This will generate a page with a list of all the pages in a folder that doesn't
already have an index.html file, this is really handy if you want to have multiple
levels of navigation.

This plugin will check your current theme for a `breadcrumbs.html` template file,
otherwise it will fallback to its default template.
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import logging
from collections import defaultdict

from ...compat import *
from ...event import event
from ...types import PageIterator
from ...path import DataDirpath


logger = logging.getLogger(__name__)


@event("configure.plugins")
def configure_plugins_breadcrumbs(event, config):
    config.setdefault("breadcrumbs_iter", PageIterator(config))


@event('context.breadcrumbs')
def configure_context_breadcrumbs(event, config):
    # we do this here so the project has a chance to set a theme
    theme_name = config.theme_name
    theme = config.theme
    if not theme.has_template("breadcrumbs"):
        dd = DataDirpath(__name__)
        config.add_themes(dd.themes_dir())
        theme_name = "breadcrumbs"

    config.setdefault("breadcrumbs_theme_name", theme_name)


@event('output.finish')
def output_breadcrumbs(event, config):
    with config.context("breadcrumbs") as config:

        d = defaultdict(list)
        for p in config.breadcrumbs_iter:
            for bc in p.url.paths:
                d[bc].append(p)

        theme = config.themes[config.breadcrumbs_theme_name]
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

