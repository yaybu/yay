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

try:
    import StringIO as io
except ImportError:  # pragma: no cover
    import io

try:
    from urllib import request
except ImportError:  # pragma: no cover
    import urllib2 as request

try:
    from urllib import parse
except ImportError:  # pragma: no cover
    import urlparse as parse

try:
    from itertools import zip_longest
except ImportError:  # pragma: no cover
    from itertools import izip_longest as zip_longest

try:
    basestring = basestring
except NameError:  # pragma: no cover
    basestring = str
