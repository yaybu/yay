# Copyright 2011 Isotoma Limited
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

from yay.nodes import Node, Boxed, Sequence

def flatten(lst):
    for itm in lst:
        if isinstance(itm, list):
            for x in flatten(itm):
               yield x
        else:
            yield itm

class Flatten(Node):

    """ Inspired by Ruby's .flatten - flatten nested lists into a single one """

    def __init__(self, value):
        self.value = value

    def semi_resolve(self, context):
        return Sequence(list(Boxed(x) for x in flatten(self.value.resolve(context))))

    def resolve(self, context):
        val = self.semi_resolve(context).resolve(context)
        return val

    def walk(self, context):
        yield self.value

