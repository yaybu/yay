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

import pkgutil

from yay.errors import NotFound, NotModified
from yay.compat import io
from .base import IOpener, etag_stream


class PackageOpener(IOpener):

    name = "packages"
    schemes = ("package://", )

    def open(self, uri, etag=None):
        package, uri = uri.lstrip("package://").split("/", 1)

        data = pkgutil.get_data(package, uri)
        if data is None:
            raise NotFound("Package '%s' could not be imported" % package)

        fp = io.StringIO(data)
        fp.len = len(data)
        fp.labels = ()

        new_etag = etag_stream(io.StringIO(data))
        if etag and new_etag == etag:
            raise NotModified("'%s' hasnt changed" % uri)
        fp.etag = new_etag
        fp.uri = uri

        return fp
