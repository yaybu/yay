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


class StringPart(object):
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

    def __getstate__(self):
        return dict(value=self.value, secret=self.secret)

    def __setstate__(self, state):
        self.value = state['value']
        self.secret = state['secret']


class String(object):
    """ I represent a string which contains sensitive parts """

    def __init__(self, parts=None):
        self.parts = []
        if parts:
            self.extend(parts)

    def add(self, value):
        if isinstance(value, String):
            self.parts.extend(value.parts)
        else:
            self.parts.append(StringPart(value, False))

    def add_secret(self, value):
        self.parts.append(StringPart(value, True))

    def extend(self, value):
        [self.add(v) for v in value]

    def as_list(self, secret=True):
        """
        Return the string parts as a list

        If secret is True (the default) then the sensitive parts of the string
        will be obfuscated. If it is False, they will not.
        """
        if secret:
            return [unicode(p.protected) for p in self.parts]
        return [unicode(p.unprotected) for p in self.parts]

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

