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
        def foo(v1, v2):
            print("once")
            return v1 + v2

        with testdata.capture(loggers=False) as c1:
            r1 = foo(1, 2)
        self.assertTrue("once" in c1)

        with testdata.capture(loggers=False) as c1:
            r2 = foo(1, 2)
        self.assertFalse("once" in c1)
        self.assertEqual(r1, r2)

        with testdata.capture(loggers=False) as c2:
            r3 = foo(3, 4)
        self.assertTrue("once" in c2)
        self.assertNotEqual(r3, r2)

        with testdata.capture(loggers=False) as c2:
            r4 = foo(3, 4)
        self.assertFalse("once" in c2)
        self.assertNotEqual(r4, r2)
        self.assertEqual(r3, r4)

    def test_inheritance(self):
        class InFoo(object):
            @property
            @once
            def bar(self):
                print("bar")
                return 10
            @classmethod
            @once
            def bar_method(cls):
                print("bar_method")
                return 12
        class InChe(InFoo): pass
        class InBoo(InChe): pass

        # instance method/property
        f = InFoo()
        with testdata.capture(loggers=False) as c:
            f.bar
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            f.bar
        self.assertFalse("bar" in c)

        che = InChe()
        with testdata.capture(loggers=False) as c:
            che.bar
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            che.bar
        self.assertFalse("bar" in c)

        b = InBoo()
        with testdata.capture(loggers=False) as c:
            b.bar
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            b.bar
        self.assertFalse("bar" in c)

        f = InBoo()
        with testdata.capture(loggers=False) as c:
            f.bar
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            f.bar
        self.assertFalse("bar" in c)

        # standalone function
        @once
        def bar_func(i):
            print("bar")
            return 11
        with testdata.capture(loggers=False) as c:
            bar_func(300)
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            bar_func(300)
        self.assertFalse("bar" in c)

        # classmethod
        with testdata.capture(loggers=False) as c:
            InFoo.bar_method()
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            InFoo.bar_method()
        self.assertFalse("bar" in c)

        with testdata.capture(loggers=False) as c:
            InChe.bar_method()
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            InChe.bar_method()
        self.assertFalse("bar" in c)

        with testdata.capture(loggers=False) as c:
            InBoo.bar_method()
        self.assertTrue("bar" in c)
        with testdata.capture(loggers=False) as c:
            InBoo.bar_method()
        self.assertFalse("bar" in c)


