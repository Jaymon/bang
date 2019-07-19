# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.compat import *
from bang.event import Events, Receipt
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
            for ret in event_name.receipt.rets:
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


