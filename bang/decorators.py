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
        print("adding")
        return x + 1

    func(4) # prints "adding"
    func(10) # prints "adding"
    func(4) # returns 5, no print
    func(10) # returns 11, no print
    """
    def __init__(self, f):
        self.f = f
        self.name = "once_{}".format(f.__name__)

    def __call__(self, *args, **kwargs):
        name = str(hash(self.f))
        if args:
            for a in args:
                name += str(hash(a))

        if kwargs:
            for k, v in kwargs.items():
                name += str(hash(k))
                name += str(hash(v))

        try:
            ret = getattr(self, name)

        except AttributeError:
            ret = self.f(*args, **kwargs)
            setattr(self, name, ret)

        return ret

