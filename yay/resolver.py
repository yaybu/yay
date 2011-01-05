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

class Resolver(object):

    """ Run .format() on all strings in a dictionary, raises a ValueError on cycles """

    def __init__(self, raw):
        self._raw = raw

    def resolve_value(self, value, label=""):
        if isinstance(value, basestring):
            return self.resolve_string(value, label)
        elif isinstance(value, dict):
            return self.resolve_dict(value, label)
        elif isinstance(value, list):
            return self.resolve_list(value, label)
        return value

    def resolve_string(self, value, label=""):
        encountered = set()
        previous = None
        while value != previous:
            if value in encountered:
                raise ValueError("Cycle encountered (%s)" % label)
            encountered.add(value)

            previous = value
            value = value.format(**self._raw)

        return value

    def resolve_list(self, lst, label=""):
        new_lst = []
        for i, item in enumerate(lst):
            new_lst.append(self.resolve_value(item, "%s[%s]" % (label,i)))
        return new_lst

    def resolve_dict(self, dct, label=""):
        new_dct = {}
        for key, value in dct.iteritems():
            key_label = label + "." + key if label else key
            new_dct[key] = self.resolve_value(value, key_label)
        return new_dct

    def resolve(self):
        return self.resolve_dict(self._raw)

