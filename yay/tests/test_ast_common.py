# Copyright 2013 Isotoma Limited
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

from yay.ast import Literal


class DynamicLiteral(Literal):

    """
    I am a literal that pretends to be dynamic for testing purposes.
    """

    def dynamic(self):
        return True


class ComplexLiteral(Literal):

    """
    I am a literal that pretends to be more complicated than I am for testing purposes.

    I can be reduced from a ComplexLiteral to a Literal.
    """

    def simplify(self):
        return Literal(self.literal)
