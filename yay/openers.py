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

import urllib, urlparse
import StringIO
import os
import subprocess

from yay.errors import NotFound


class IOpener(object):

    def open(self, uri):
        """ Given a uri, return a YAML compatible stream """
        pass


class FileOpener(IOpener):

    scheme = "file://"

    def open(self, uri):
        if uri.startswith("file://"):
            uri = uri[8:]
        return open(uri, "r")


class UrlOpener(IOpener):

    scheme = "http://"

    def open(self, uri):
        return urllib.urlopen(uri)


class MemOpener(IOpener):

    """
    This is purely a testing stub.

    It has a class-shared dictionary called 'data', where keys are uris and
    values are data to return as a StringIO when open() is called. This means
    test cases can exercise the yay extends machinery without the need to create
    temporary files
    """

    scheme = "mem://"
    data = {}

    def open(self, uri):
        return StringIO.StringIO(self.data[uri])

    @classmethod
    def add(cls, uri, data):
        cls.data[uri] = data

    @classmethod
    def reset(cls):
        cls.data = {}


class Gpg(object):

    def filter(self, fp):
        data = fp.read()
        p = subprocess.Popen(["gpg", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = p.communicate(data)
        stream = StringIO.StringIO(stdout)
        stream.secret = True
        return stream


class Openers(object):

    def __init__(self, searchpath=None):
        self.searchpath = searchpath or []

        self.openers = {}
        for cls in IOpener.__subclasses__():
            self.openers[cls.scheme] = cls()

    def _scheme(self, uri):
        parsed = urlparse.urlparse(uri)
        return parsed.scheme

    def _absolute(self, uri):
        return self._scheme(uri) or uri.startswith("/")

    def _relative(self, uri):
        return not self._absolute(uri)

    def _join(self, *uri):
        if self._scheme(uri[0]):
            return urlparse.urljoin(*uri)
        return os.path.join(*uri)

    def _open(self, uri):
        for scheme, opener in self.openers.iteritems():
            if uri.startswith(scheme):
                return opener.open(uri)

    def open(self, uri):
        fp = None

        if self._absolute(uri):
            fp = self._open(uri)
        else:
            for path in self.searchpath:
                fp = self._open(self._join(path, uri))
                if fp:
                    break
            else:
                # Support direct file paths that dont specify a scheme
                if os.path.exists(uri):
                    fp = self.openers["file://"].open(uri)

        if not fp:
            raise NotFound("'%s' could not be found" % uri)

        if uri.endswith(".gpg"):
            fp = Gpg().filter(fp)

        return fp

