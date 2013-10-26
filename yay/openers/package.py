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

import os
import sys

from yay.errors import NotFound
from .base import IOpener, FileOpener


class PackageOpener(IOpener):

    name = "packages"
    schemes = ("package://", )

    def open(self, uri, etag=None):
        package, uri = uri.lstrip("package://").split("/", 1)
        try:
            __import__(package)
            module = sys.modules[package]
        except ImportError:
            raise NotFound("Package '%s' could not be imported" % package)
        path = os.path.join(os.path.dirname(module.__file__), uri)
        return FileOpener().open(path, etag)
