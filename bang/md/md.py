"""
in this module, we fix all the problems with markdown's default code display stuff

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

http://pythonhosted.org/Markdown/extensions/api.html

https://github.com/waylan/Python-Markdown/wiki/Third-Party-Extensions
"""
import re
import os

from markdown.extensions import codehilite, fenced_code, Extension
from markdown.inlinepatterns import SimpleTagPattern
from markdown import util

from markdown.extensions.footnotes import FootnoteExtension as BaseFootnoteExtension, \
    FootnotePattern as BaseFootnotePattern

from markdown.inlinepatterns import ImagePattern as BaseImagePattern, \
    ImageReferencePattern as BaseImageReferencePattern

from markdown.treeprocessors import Treeprocessor
from markdown.blockprocessors import BlockProcessor
from . import event


