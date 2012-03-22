#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

class memoize(object):
    """Implements a memoize decorator for instance methods.

    The memoize decorator caches the results of the invocation of an instance
    method.

    This decorator class is by Oleg Noga and was found at

        http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/

    The original snippet by Oleg Noga can be found here

        http://code.activestate.com/recipes/466320-another-memoize/#c7

    """
    def __init__(self, function):
        self._function = function
        self._cacheName = '_cache__' + function.__name__
    def __get__(self, instance, cls=None):
        self._instance = instance
        return self
    def __call__(self, *args):
        cache = self._instance.__dict__.setdefault(self._cacheName, {})
        if cache.has_key(args):
            return cache[args]
        else:
            object = cache[args] = self._function(self._instance, *args)
            return object
