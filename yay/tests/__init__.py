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


from yay.tests import (  # noqa
    test_ast,
    test_ast_common,
    test_ast_multiline,
    test_config,
    test_lexer,
    test_openers,
    test_parser,
    test_parser_errors,
    test_resolve,
    test_resolve_cycles,
    test_resolve_paradoxes,
    test_test_manifest,
    test_transform,
)

__all__ = [m for m in list(globals()) if m.startswith("test_")]
