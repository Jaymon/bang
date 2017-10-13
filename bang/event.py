# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle

from collections import defaultdict


logger = logging.getLogger(__name__)


class Receipt(object):
    @classmethod
    def get_key(cls, event_name, callback_args, callback_kwargs):

        vargs = []
        for a in callback_args:
            if isinstance(a, dict):
                vargs.append(a.keys())

            elif isinstance(a, object):
                vargs.append(id(a))

            else:

        val = {
            "event_name": event_name,
            "args": list(callback_args),
            "kwargs": callback_kwargs.keys()
        }
        return hashlib.md5(pickle.dumps(val, pickle.HIGHEST_PROTOCOL)).hexdigest()

    def __init__(self, event_name, callback_args=None, callback_kwargs=None, key=""):
        self.event_name = event_name
        self.args = callback_args if callback_args else ()
        self.kwargs = callback_kwargs if callback_kwargs else {}
        self.key = key if key else self.get_key(self.event_name, self.args, self.kwargs)
        self.callbacks = {}

    def add(self, callback, ret=None):
        self.callbacks[callback] = ret

    def __contains__(self, callback):
        return callback in self.callbacks

    def __len__(self):
        return len(self.callbacks)

    def run(self, callback):
        if callback in self:
            ret = self.callbacks[callback]
        else:
            ret = callback(self.event_name, *self.args, **self.kwargs)
            self.add(callback, ret)
        return ret


class Events(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.bound = defaultdict(list)
        self.receipts = defaultdict(dict)

    def push(self, event_name, *args, **kwargs):
        """Similar to broadcast but if any new callbacks are bound to the event_name
        those will be run on the binding"""
        #receipt = super(Events, self).broadcast(event_name, *args, **kwargs)
        key = Receipt.get_key(event_name, args, kwargs)
        pout.v(key)
        if event_name in self.receipts and key in self.receipts[event_name]:
            receipt = self.receipts[event_name][key]
        else:
            receipt = Receipt(event_name, args, kwargs, key=key)

        receipt = self.run(receipt)
        self.receipts[event_name][key] = receipt
        #pout.v(self.receipts)
        return receipt

    def broadcast(self, event_name, *args, **kwargs):
        receipt = Receipt(event_name, args, kwargs)
        return self.run(receipt)

    def run(self, receipt):
        callbacks = self.bound.get(receipt.event_name, [])
        if len(callbacks) > 0:
            logger.info("Event {} broadcasting to {} callbacks".format(receipt.event_name, len(callbacks)))

            for callback in callbacks:
                receipt.run(callback)
                logger.debug("Event {} broadcast to {} callback".format(receipt.event_name, callback))

        else:
            logger.debug("Event {} ignored".format(receipt.event_name))

        return receipt

    def bind(self, event_name, callback):
        self.bound[event_name].append(callback)

        # event has been pushed previously so go ahead and run this callback 
        # We do this because we primarily use events to configure everything and
        # sometimes there is a chicken/egg problem where code will push an event
        # before the block that will handle that event is bound, but we need that
        # callback to be run when it is bound even though it's missed the original
        # broadcast, so any events that use the push method will be run when new
        # callbacks are added
        if event_name in self.receipts:
            for receipt in self.receipts[event_name].values():
                receipt.run(callback)

    def __contains__(self, event_name):
        return event_name in self.bound

    def __call__(event_name, *event_names):
        """decorator that wraps the bind() method to make it easier to bind functions
        to an event"""
        def wrap(callback):
            self.bind(event_name, callback)
            for en in event_names:
                self.bind(en, callback)

            return callback

        return wrap


# !!! I can't decide if I like event or events as the primary interface
events = Events()
event = events

