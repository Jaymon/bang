# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import warnings


class classproperty(property):
    """creat a class property

    :Example:
        class Foo(object):
            @classproperty
            def bar(cls):
                return 42
        Foo.bar # 42
    """
    def __get__(self, instance, cls):
        return self.fget(cls)


def deprecated(func):
    def wrapped(*args, **kwargs):
        # https://wiki.python.org/moin/PythonDecoratorLibrary#Generating_Deprecation_Warnings
        # http://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
        warnings.warn_explicit(
            "deprecated function {}".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )

        return func(*args, **kwargs)
    return wrapped


class once(object):
    """run the decorated function only once

    @once
    def func(x):
        return x + 1

    func(4) # return 5
    func(10) # return 5
    func.reset()
    func(10) # return 11
    """
    def __init__(self, f):
        self.f = f
        self.reset()

    def __call__(self, *args, **kwargs):
        if not self.called:
            self.ret = self.f(*args, **kwargs)
        self.called = True
        return self.ret

    def reset(self):
        self.called = False
        self.ret = None

