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


