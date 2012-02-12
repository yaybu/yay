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

import urllib
import urlparse
import StringIO
import os
import sys
import subprocess

from yay.errors import NotFound


class IOpener(object):

    def open(self, uri):
        """ Given a uri, return a YAML compatible stream """
        pass


class FpAdaptor(object):

    def __init__(self, fp):
        self.fp = fp

    def __getattr__(self, key):
        """Everything delegated to the object"""
        return getattr(self.fp, key)


class FileOpener(IOpener):

    schemes = ("file://", )

    def open(self, uri):
        if uri.startswith("file://"):
            uri = uri[8:]
        if not os.path.exists(uri):
            raise NotFound("Local file '%s' could not be found" % uri)

        class File(FpAdaptor):
            @property
            def len(self):
                return int(os.fstat(self.fp.fileno())[6])

        return File(open(uri, "rb"))


class PackageOpener(IOpener):

    schemes = ("package://", )

    def open(self, uri):
        package, uri = uri.lstrip("package://").split("/", 1)
        try:
            __import__(package)
            module = sys.modules[package]
        except ImportError:
            raise NotFound("Package '%s' could not be imported")
        module_path = os.path.dirname(module.__file__)
        path = os.path.join(module_path, uri)
        return FileOpener().open(path)


class HomeOpener(IOpener):

    schemes = ("home://", )

    def open(self, uri):
        uri = os.path.expanduser("~/" + uri.lstrip("home://"))
        return FileOpener().open(uri)


class UrlOpener(IOpener):

    schemes = ("http://", "https://")

    def open(self, uri):
        fp = urllib.urlopen(uri)
        if fp.getcode() != 200:
            raise NotFound("URL '%s' could not be found (HTTP response %s)" % (uri, fp.getcode()))

        class Resource(FpAdaptor):
            @property
            def len(self):
                return int(self.fp.info()['content-length'])

        return Resource(fp)


class MemOpener(IOpener):

    """
    This is purely a testing stub.

    It has a class-shared dictionary called 'data', where keys are uris and
    values are data to return as a StringIO when open() is called. This means
    test cases can exercise the yay extends machinery without the need to create
    temporary files
    """

    schemes = ("mem://", )
    data = {}

    def open(self, uri):
        fp = StringIO.StringIO(self.data[uri])
        fp.len = len(self.data[uri])
        return fp

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
        stream.len = len(stdout)
        stream.secret = True
        return stream


class Openers(object):

    def __init__(self, searchpath=None):
        self.searchpath = searchpath or []

        self.openers = []
        for cls in IOpener.__subclasses__():
            self.openers.append(cls())

    def _scheme(self, uri):
        parsed = urlparse.urlparse(uri)
        return parsed.scheme

    def _absolute(self, uri):
        return self._scheme(uri)

    def _relative(self, uri):
        return not self._absolute(uri)

    def _join(self, *uri):
        if self._scheme(uri[0]):
            retval = uri[0]
            for part in uri[1:]:
                retval = retval.rstrip("/") + "/" + part.lstrip("/")
            return retval
        return os.path.join(*uri)

    def _open(self, uri):
        for opener in self.openers:
            for scheme in opener.schemes:
                if uri.startswith(scheme):
                    return opener.open(uri)

        return FileOpener().open(uri)

    def open(self, uri):
        fp = None

        if uri.startswith("/"):
            fp = FileOpener().open(uri)
        elif self._absolute(uri):
            fp = self._open(uri)
        else:
            for path in self.searchpath:
                try:
                    fp = self._open(self._join(path, uri))
                    break
                except NotFound:
                    pass

        if not fp:
            raise NotFound("'%s' could not be found" % uri)

        if uri.endswith(".gpg"):
            fp = Gpg().filter(fp)

        return fp

