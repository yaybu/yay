# Copyright 2010-2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect

from yay.nodes import Node
from yay import String

class Unboxable(Exception):
    pass


class BoxingFactory(object):

    """ Sometimes we need to box complicated types that we might have special
    nodes for wrapping. The BoxingFactory will wrap any special nodes in the
    right wrapper type before falling back to the Boxed() wrapping method. """

    boxers = []

    @classmethod
    def register(cls, checker, boxer):
        cls.boxers.append((checker, boxer))

    @classmethod
    def box(cls, value):
        for checker, boxer in cls.boxers:
            if checker(value):
                return boxer(value)
        return Boxed(value)


def callable_boxer(val):
    """ Attempt to box callables """
    try:
        #inspect.getcallargs(val)
        return BoxingFactory.box(val())
    except TypeError:
        raise Unboxable("Cannot invoke callable that requires arguments")
BoxingFactory.register(callable, callable_boxer)


class Boxed(Node):
    """
    A Boxed node is some sort of literal and uninteresting value that
    is wrapped simply so we can put it in the graph

    """

    def __init__(self, value):
        self.value = value

    secret = False

    def resolve(self):
        """
        Boxed will do some simple and automatic processing of data when it
        resolves.

          * If it isn't a subclass of basestring it will be returned as is
          * `yes`, `true` and `on` will become python True
          * `no`, `false` and `off` will become python False
          * If it can be cast to an ``int`` it will be.
          * If it can be represented in ascii it will be
          * Otherwise a unicode string is returned
        """
        value = self.value

        if not isinstance(value, basestring):
            return value

        if self.secret:
            p = String()
            p.add_secret(value)
            return p

        if value.lower() in ("yes", "true", "on"):
            return True
        if value.lower() in ("no", "false", "off"):
            return False

        try:
            return int(value)
        except ValueError:
            pass

        #FIXME: could still be a float or a timestamp

        try:
            return value.encode('ascii')
        except UnicodeEncodeError:
            return value

    def get(self, key):
        """
        If the boxed value implements a list or dict like value access mechanism
        a Boxed node will allow those inner values to be boxed on demand so Yay
        can access them
        """
        if isinstance(self.value, list):
            return BoxingFactory.box(self.value[key])

        if hasattr(self.value, "get"):
            return BoxingFactory.box(self.value.get(key))

        if hasattr(self.value, key):
            return BoxingFactory.box(getattr(self.value, key))

        self.error("Unable to find '%s'" % key)

    def __repr__(self):
        return "Boxed(%s)" % self.value

    def clone(self):
        return Boxed(self.value)

