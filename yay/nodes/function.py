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

from yay.nodes import Boxed

class Function(object):

    def __init__(self, function, args):
        self.function = function
        self.args = args

    def resolve(self, context):
        args = [arg.resolve(context) for arg in self.args]
        return context.call(self.function, args)

    def semi_resolve(self, context):
        return [Boxed(x) for x in self.resolve(context)]

    def __repr__(self):
        return "Function(%s)" % ", ".join([self.function] + [str(a) for a in self.args])
