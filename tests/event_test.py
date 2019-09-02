# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.compat import *
from bang.event import Events, Extend
from bang.types import Page
from . import TestCase


class EventsTest(TestCase):
    def test_push_and_bind(self):
        ev = Events()
        c = self.get_config()

        @ev("push_and_bind")
        def push1(event, config):
            event.text += "1"

        r1 = ev.push("push_and_bind", c, text="1")

        @ev("push_and_bind")
        def push2(event, config):
            event.text += "2"

        r2 = ev.push("push_and_bind", c, text="2")

        @ev("push_and_bind")
        def push3(event, config):
            event.text += "3"

        #pout.v(r1.text, r2.text, r1.event_callbacks, r2.event_callbacks)

        self.assertEqual("1123", r1.text)
        self.assertEqual("2123", r2.text)

    def test_broadcast(self):
        ev = Events()
        config = self.get_config()

        r = ev.broadcast("foo", config, count=0)
        self.assertEqual(0, r.count)

        def cb1(event, config):
            event.count += 1
        ev.bind("foo", cb1)

        r = ev.broadcast("foo", config, count=0)
        self.assertEqual(1, r.count)

        r = ev.broadcast("foo", config, count=r.count)
        self.assertEqual(2, r.count)

    def test_once(self):
        ev = Events()
        config = self.get_config()

        @ev("once")
        def once1(event, config):
            pass

        @ev("once")
        def once2(event, config):
            pass

        with self.assertLogs(level="DEBUG") as c:
            ev.once("once", config)
        logs = "\n".join(c[1])
        self.assertTrue("once1" in logs)
        self.assertTrue("once2" in logs)

        with self.assertLogs(level="DEBUG") as c:
            ev.once("once", config)
        logs = "\n".join(c[1])
        self.assertTrue("ignored" in logs)

        @ev("once")
        def once3(event, config):
            pass

        with self.assertLogs(level="DEBUG") as c:
            ev.once("once", config)
        logs = "\n".join(c[1])
        self.assertFalse("once1" in logs)
        self.assertFalse("once2" in logs)
        self.assertTrue("once3" in logs)

        with self.assertLogs(level="DEBUG") as c:
            ev.once("once", config)
        logs = "\n".join(c[1])
        self.assertTrue("ignored" in logs)


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




