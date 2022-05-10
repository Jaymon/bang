# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging
import inspect
import types

from collections import defaultdict

from .compat import *


logger = logging.getLogger(__name__)


class Event(object):
    """An instance of this class is passed as the first argument to any callback
    when an event is broadcast, this looks and acts just like a normal string
    instance so it can be interchangeable with event_name"""
    def __init__(self, event_name, config, **kwargs):
        self.event_name = event_name
        self.event_callbacks = []
        self.event_keys = list(kwargs.keys())

        self.config = config
        for k, v in kwargs.items():
            setattr(self, k, v)


class Events(object):
    """Singleton. The main interface for interacting with events

    you add events with .bind() and run events using either .broadcast() or .push()

    :Example:
        @event("EVENT_NAME")
        def callback(event, config):
            # every callback takes an event and callback instance
            pass

        event.broadcast("EVENT_NAME", config, foo=1)
        # in the callback foo will be accessible through event.foo
    """
    def __init__(self):
        # this will hold any callbacks bound to an event_name through .bind
        self.bound = defaultdict(list)

        # this will hold Event instances under event_name keys that have been
        # broadcast through the .push() method
        self.pushed = defaultdict(list)
        self.onced = defaultdict(list)
        #self.onced = {}

    def push(self, event_name, config, **kwargs):
        """Similar to broadcast but if any new callbacks are bound to the event_name
        those will be run on the binding so it can pick up straggler bind calls

        .push() is used primarily for configure events to make order of events a
        little less important while configuring everything, after configuration,
        most events are done using .broadcast()

        :param event_name: string, the event name whose callbacks should be ran
        :param config: Config instance, the current project configuration
        :param **kwargs: key=val values that will be accessible in the Event instance
            passed to the callbacks
        :returns: an Event instance
        """
        event = self.broadcast(event_name, config, **kwargs)
        self.pushed[event_name].append(event)
        return event

    def once(self, event_name, config, **kwargs):
        """Similar to broadcast but all the bound events for event_name will only
        be ran once and only once

        trigger might be an ok name for this also

        :param event_name: string, the event name whose callbacks should be ran
        :param config: Config instance, the current project configuration
        :param **kwargs: key=val values that will be accessible in the Event instance
            passed to the callbacks
        :returns: an Event instance
        """
        event = self.broadcast(event_name, config, **kwargs)

        # remove the callbacks from bound and add them to the once history so
        # they won't be ran again on subsequent calls
        callbacks = self.bound.pop(event_name, [])
        self.onced[event_name].extend(callbacks)

        return event

    def broadcast(self, event_name, config, **kwargs):
        """broadcast event_name to all bound callbacks

        :param event_name: string, the event name whose callbacks should be ran
        :param config: Config instance, the current project configuration
        :param **kwargs: key=val values that will be accessible in the Event instance
            passed to the callbacks
        :returns: an Event instance
        """
        event = Event(event_name, config, **kwargs)
        callbacks = self.bound.get(event_name, [])
        if len(callbacks) > 0:
            logger.info("Event [{}] broadcasting to {} callbacks".format(event_name, len(callbacks)))

            for callback in callbacks:
                self.run(event, callback)

        else:
            logger.debug("Event [{}] ignored".format(event_name))

        return event

    def run(self, event, callback):
        """Runs callback with the event instance

        :param event: Event instance, the event instance that holds all the information
            and keyword arguments that were passed to the broadcast method
        :param callback: callable, the callback that will be ran
        :returns: the same Event instance
        """
        event_name = event.event_name

        callback(event, event.config)
        event.event_callbacks.append(callback)
        logger.debug("Event [{}] running {} callback".format(event_name, callback))

        return event

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
        if event_name in self.pushed:
            for event in self.pushed[event_name]:
                self.run(event, callback)

    def __call__(self, *event_names):
        """decorator that wraps the bind() method to make it easier to bind functions
        to an event

        :Example:
            event = Events()

            @event("event_name")
            def callback(event, config):
                pass
        """
        def wrap(callback):
            for en in event_names:
                self.bind(en, callback)

            return callback

        return wrap

    def reset(self):
        self.bound.clear()
        self.pushed.clear()


class Extend(object):
    """you can use this decorator to extend instances in the bangfile with custom
    functionality

    :Example:
        from event import extend

        class Foo(object): pass

        @extend(Foo, "bar")
        def bar(self, n1, n2):
            return n1 + n2

        f = Foo()
        f.bar(1, 2) # 3

        @extend(f, "che")
        @property
        def che(self):
            return 42

        f.che # 42
    """
    def property(self, o, name):
        """decorator to extend o with a property at name

        Using this property method is equivalent to:
            @extend(o, "NAME")
            @property
            def name(self):
                return 42

        :param o: instance|class, the object being extended
        :param name: string, the name of the property
        :returns: callable wrapper
        """
        def wrap(callback):
            if inspect.isclass(o):
                self.patch_class(o, name, property(callback))

            else:
                #self.patch_class(o.__class__, name, property(callback))
                self.patch_instance(o, name, property(callback))

            return callback
        return wrap

    def method(self, o, name):
        """decorator to extend o with method name

        :param o: instance|class, the object being extended
        :param name: string, the name of the method
        :returns: callable wrapper
        """
        return self(o, name)

    def __call__(self, o, name):
        """shortcut to using .property() or .method() decorators"""
        def wrap(callback):
            if inspect.isclass(o):
                self.patch_class(o, name, callback)

            else:
                self.patch_instance(o, name, callback)

            return callback
        return wrap

    def patch_class(self, o, name, callback):
        """internal method that patches a class o with a callback at name"""
        setattr(o, name, callback)

    def patch_instance(self, o, name, callback):
        """internal method that patches an instance o with a callback at name"""
        if isinstance(callback, property):
            setattr(o.__class__, name, callback)
        else:
            setattr(o, name, types.MethodType(callback, o))


event = Events()
extend = Extend()

