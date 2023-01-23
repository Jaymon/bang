# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

from bang import event

@event('configure.theme')
def theme_config(event_name, config):
    pass

