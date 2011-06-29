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


class ProtectedStringPart(object):
    """ I represent a portion of a string which may or may not be sensitive """

    __slots__ = ("value", "secret", )

    def __init__(self, value, secret):
        self.value = value
        self.secret = secret

    @property
    def protected(self):
        if self.secret:
            return "*" * 5
        return self.value

    @property
    def unprotected(self):
        return self.value


class _ProtectedString(object):
    """ I exist purely to fudge around MRO """
    pass


class ProtectedString(_ProtectedString, basestring):
    """ I represent a string which contains sensitive parts """

    def __init__(self, parts=None):
        self.parts = []
        if parts:
            self.parts.extend(parts)

    def add(self, value):
        if isinstance(value, ProtectedString):
            self.parts.extend(value.parts)
        else:
            self.parts.append(ProtectedStringPart(value, False))

    def add_secret(self, value):
        self.parts.append(ProtectedStringPart(value, True))

    def __str__(self):
        return "".join([str(p.protected) for p in self.parts])

    def __unicode__(self):
        return u"".join([unicode(p.protected) for p in self.parts])

    @property
    def protected(self):
        return u"".join([unicode(p.protected) for p in self.parts])

    @property
    def unprotected(self):
        return u"".join([unicode(p.unprotected) for p in self.parts])

