# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from collections import defaultdict

from .compat import *


logger = logging.getLogger(__name__)


class Receipt(object):
    """Aggregator of all the return values for all the callbacks ran on event_name

    this makes it so you can get the return values from all the previously ran callbacks
    """
    @property
    def returns(self):
        """Return all the return values collected in this receipt"""
        return self.callbacks.values()

    def __init__(self, event_name, callback_args=None, callback_kwargs=None):
        self.event_name = event_name
        self.event = Event(event_name, self)
        self.args = callback_args or ()
        self.kwargs = callback_kwargs or {}
        self.callbacks = {}

    def add(self, callback, ret=None):
        self.callbacks[callback] = ret

    def __contains__(self, callback):
        return callback in self.callbacks

    def __len__(self):
        return len(self.callbacks)

    def run(self, callback):
        """run callback and save its return value"""
        if callback in self:
            ret = self.callbacks[callback]
        else:
            ret = callback(self.event, *self.args, **self.kwargs)
            self.add(callback, ret)
        return ret


class Event(String):
    """An instance of this class is passed as the first argument to any callback
    when an event is broadcast, this looks and acts just like a normal string
    instance so it can be interchangeable with event_name"""
    def __new__(cls, event_name, receipt):
        instance = super(Event, cls).__new__(cls, event_name)
        instance.receipt = receipt
        return instance


class Events(object):
    """Singleton. The main interface for interacting with events

    you add events with .bind() and run events using either .broadcast() or .push()
    """
    def __init__(self):
        self.bound = defaultdict(list)
        self.receipts = defaultdict(list)

    def push(self, event_name, *args, **kwargs):
        """Similar to broadcast but if any new callbacks are bound to the event_name
        those will be run on the binding so it can pick up straggler bind calls"""
        receipt = self.broadcast(event_name, *args, **kwargs)
        self.receipts[event_name].append(receipt)
        return receipt

    def broadcast(self, event_name, *args, **kwargs):
        """broadcast event_name to all bound callbacks

        this creates a Receipt instance that binds *args and **kwargs to event_name
        so if pushed was used any additional .bind() calls of event_name will be
        run with *args, **kwargs
        """
        receipt = Receipt(event_name, args, kwargs)
        return self.run(receipt)

    def run(self, receipt):
        """calls receipt.run(callback) for all the callbacks bound to receipt.event_name

        :param receipt: Receipt instance, where the return values from the callbacks
            will be stored
        :returns: Receipt instance, basically the same instance that was passed in
        """
        callbacks = self.bound.get(receipt.event_name, [])
        if len(callbacks) > 0:
            logger.info("Event [{}] broadcasting to {} callbacks".format(receipt.event_name, len(callbacks)))

            for callback in callbacks:
                receipt.run(callback)
                logger.debug("Event [{}] broadcast to {} callback".format(receipt.event_name, callback))

        else:
            logger.debug("Event [{}] ignored".format(receipt.event_name))

        return receipt

    def bind(self, event_name, callback):
        """binds callback to event_name

        :param event_name: string, the event name
        :param callback: callable, typically, the callback should accept (event, *args, **kwargs)
        """
        self.bound[event_name].append(callback)

        # event has been pushed previously so go ahead and run this callback 
        # We do this because we primarily use events to configure everything and
        # sometimes there is a chicken/egg problem where code will push an event
        # before the block that will handle that event is bound, but we need that
        # callback to be run when it is bound even though it's missed the original
        # broadcast, so any events that use the push method will be run when new
        # callbacks are added
        if event_name in self.receipts:
            for receipt in self.receipts[event_name]:
                receipt.run(callback)

    def __contains__(self, event_name):
        return event_name in self.bound

    def __call__(self, event_name, *event_names):
        """decorator that wraps the bind() method to make it easier to bind functions
        to an event

        :Example:
            event = Events()

            @event("event_name")
            def callback(event, *args, **kwargs):
                pass
        """
        def wrap(callback):
            self.bind(event_name, callback)
            for en in event_names:
                self.bind(en, callback)

            return callback

        return wrap


event = Events()

