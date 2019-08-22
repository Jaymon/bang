# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.compat import *
from bang.event import Events, Receipt, Extend
from bang.types import Page
from . import TestCase


class ReceiptTest(TestCase):
    def test_callback_uniqueness(self):
        def cb1(*args, **kwargs): pass
        def cb2(*args, **kwargs): pass

        r = Receipt("foo", [1], {"key": "val"})

        r.add(cb1)
        self.assertEqual(1, len(r))

        r.add(cb2)
        self.assertEqual(2, len(r))

        r.add(cb2)
        self.assertEqual(2, len(r))

    def test_run(self):
        count = {"": 0}
        def cb1(*args, **kwargs): count[""] += 1
        def cb2(*args, **kwargs): count[""] += 1

        r = Receipt("foo")
        r.run(cb1)
        self.assertEqual(1, count[""])

        r.run(cb1)
        self.assertEqual(1, count[""])

        r.run(cb2)
        self.assertEqual(2, count[""])

    def test_event(self):
        def cb1(*args, **kwargs): return 1
        def cb2(event_name):
            for ret in event_name.receipt.returns:
                if ret == 1:
                    return ret
            return 2

        r = Receipt("foo")
        r.run(cb1)
        ret = r.run(cb2)
        self.assertEqual(1, ret)


class EventsTest(TestCase):
    def test_broadcast(self):
        ev = Events()
        count = {"": 0}
        def cb1(ev, count): count[""] += 1

        ev.broadcast("foo", count)
        self.assertEqual(0, count[""])

        ev.bind("foo", cb1)
        ev.broadcast("foo", count)
        self.assertEqual(1, count[""])

        ev.broadcast("foo", count)
        self.assertEqual(2, count[""])

    def test_push(self):
        ev = Events()
        count = {"": 0}
        def cb1(ev, count): count[""] += 1

        ev.push("foo", count)
        self.assertEqual(0, count[""])

        ev.bind("foo", cb1)
        self.assertEqual(1, count[""])

        ev.push("foo", count)
        self.assertEqual(2, count[""])



class ExtendTest(TestCase):
    def test_property(self):
        c = self.create_config()
        ex = Extend()

        self.assertEqual(None, c.foo_test)

        @ex.property(c, "foo_test")
        def foo_test(self):
            return 42
        self.assertEqual(42, c.foo_test)

        @ex(c, "foo_test")
        @property
        def foo2_test(self):
            return 43
        self.assertEqual(43, c.foo_test)

    def test_method(self):
        c = self.create_config()
        ex = Extend()

        with self.assertRaises(TypeError):
            c.foo(1, 2)

        @ex.method(c, "foo")
        def foo(self, n1, n2):
            return n1 + n2
        self.assertEqual(3, c.foo(1, 2))

        @ex(c, "foo")
        def foo2(self, n1, n2):
            return n1 * n2
        self.assertEqual(2, c.foo(1, 2))

    def test_class(self):
        extend = Extend()
        class Foo(object): pass

        @extend(Foo, "bar")
        def bar(self, n1, n2):
            return n1 + n2

        f = Foo()
        self.assertEqual(3, f.bar(1, 2))

        @extend(f, "che")
        @property
        def che(self):
            return 42

        self.assertEqual(42, f.che)

        @extend(Foo, "boo")
        def boo(self):
            return 43
        self.assertEqual(43, f.boo())

    def test_inheritance(self):
        extend = Extend()
        class FooPage(Page):
            def __init__(self): pass

        @extend(Page, "bar")
        def bar(self, n1, n2):
            return n1 + n2

        f = FooPage()
        self.assertEqual(3, f.bar(1, 2))




