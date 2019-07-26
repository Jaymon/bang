# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

import testdata

from bang.compat import *
from bang.decorators import once
from . import TestCase


class OnceTest(TestCase):
    def test_call(self):

        @once
        def foo(*args, **kwargs):
            print("This should only be seen once")
            return 5

        with testdata.capture(loggers=False) as c1:
            r1 = foo(1, 2)
        with testdata.capture(loggers=False) as c2:
            r2 = foo(3, 4)
        #pout.v(r1, r2, String(c1), String(c2))
        self.assertEqual(r1, r2)
        self.assertNotEqual(String(c1), String(c2))

        foo.reset()
        with testdata.capture(loggers=False) as c3:
            r3 = foo(1, 2)
        self.assertEqual(r1, r3)
        self.assertEqual(String(c1), String(c3))

