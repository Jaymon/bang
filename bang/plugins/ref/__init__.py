# -*- coding: utf-8 -*-
"""
Markdown reference plugin

This adds an <PROJECT-OUTPUT-DIR>/ref/index.html file that shows what each
markdown element will look like with your chosen theme. This was part of my
custom theme I use for my website and also in the default theme, it didn't make
sense to keep updating it in two spots when I made improvements so this plugin
was born.

You can use this by importing it into your project's bangfile:

    from bang.plugins import ref
"""

from ...event import event
from ...path import DataDirpath


@event("configure.plugins")
def compile_ref(event):
    event.config.project.input_dirs.append(
        DataDirpath(__name__).child_dir("input")
    )

