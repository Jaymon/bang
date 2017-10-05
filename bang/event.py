# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging


events = {}


logger = logging.getLogger(__name__)


def bind(event_name, *event_names):
    """decorator that wraps the listen() method to make it easier to bind functions
    to an event"""
    def wrap(callback):
        listen(event_name, callback)
        for en in event_names:
            listen(en, callback)

        return callback

    return wrap


def listen(event_name, callback):
    global events

    events.setdefault(event_name, [])
    events[event_name].append(callback)


def broadcast(event_name, *args, **kwargs):
    global events

    ret = None

    callbacks = events.get(event_name, [])
    if len(callbacks) > 0:
        logger.info("Event {} broadcast to {} callbacks".format(event_name, len(callbacks)))

        for callback in callbacks:
            ret = callback(event_name, *args, **kwargs)

            # callback handling works by return value introspection, if your callback
            # returns True or anything that's not None or False, it will short-circuit
            # the remaining callbacks to be run and return that value, otherwise it
            # will continue running callbacks
            if ret is not False and ret is not None:
                break

    else:
        logger.debug("Event {} ignored".format(event_name))

    return ret

