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

import urllib2
import urlparse
import StringIO
import os
import sys
import subprocess
import hashlib

from yay.errors import NotFound, NotModified

def etag_stream(fp):
    s = hashlib.sha1()
    while True:
        block = fp.read(8192)
        if not block:
            break
        s.update(block)
    return s.hexdigest()


class IOpener(object):

    def open(self, uri, etag=None):
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

    def open(self, uri, etag=None):
        if uri.startswith("file://"):
            uri = uri[8:]
        if not os.path.exists(uri):
            raise NotFound("Local file '%s' could not be found" % uri)

        class File(FpAdaptor):
            @property
            def len(self):
                return int(os.fstat(self.fp.fileno())[6])

        fp = open(uri, "rb")
        new_etag = etag_stream(fp)

        if etag and etag == new_etag:
            fp.close()
            raise NotModified("File '%s' not modified" % uri)

        fp.seek(0)
        f = File(fp)
        f.etag = new_etag
        return f


class PackageOpener(IOpener):

    schemes = ("package://", )

    def open(self, uri, etag=None):
        package, uri = uri.lstrip("package://").split("/", 1)
        try:
            __import__(package)
            module = sys.modules[package]
        except ImportError:
            raise NotFound("Package '%s' could not be imported")
        module_path = os.path.dirname(module.__file__)
        path = os.path.join(module_path, uri)
        return FileOpener().open(path, etag)


class HomeOpener(IOpener):

    schemes = ("home://", )

    def open(self, uri, etag=None):
        uri = os.path.expanduser("~/" + uri.lstrip("home://"))
        return FileOpener().open(uri, etag)


class UrlOpener(IOpener):

    schemes = ("http://", "https://")

    def open(self, uri, etag=None):
        req = urllib2.Request(uri)
        if etag:
            req.add_header("If-None-Match", etag)

        try:
            fp = urllib2.urlopen(req)

        except urllib2.URLError as exc:
            raise NotFound("URL '%s' not found (URLError)" % uri)

        except urllib2.HTTPError as exc:
            if exc.code == 304:
                raise NotModified("URL '%s' has not been modified" % uri)
            raise NotFound("URL '%s' could not be found (HTTP response %s)" % (uri, exc.code))

        class Resource(FpAdaptor):
            @property
            def etag(self):
                info = self.fp.info()
                if "etag" in info:
                    return info["etag"]
                return None

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

    def open(self, uri, etag=None):
        try:
            fp = StringIO.StringIO(self.data[uri])
        except KeyError:
            raise NotFound("Memory cell '%s' does not exist" % uri)

        fp.len = len(self.data[uri])

        new_etag = etag_stream(StringIO.StringIO(self.data[uri]))
        if etag and new_etag == etag:
            raise NotModified("Memory cell '%s' hasn't changed" % uri)
        fp.etag = new_etag

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
        stream.etag = fp.etag
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

    def _open(self, uri, etag=None):
        for opener in self.openers:
            for scheme in opener.schemes:
                if uri.startswith(scheme):
                    return opener.open(uri, etag)

        return FileOpener().open(uri, etag)

    def open(self, uri, etag=None):
        fp = None

        if uri.startswith("/"):
            fp = FileOpener().open(uri, etag)
        elif self._absolute(uri):
            fp = self._open(uri)
        else:
            for path in self.searchpath:
                try:
                    fp = self._open(self._join(path, uri), etag)
                    break
                except NotFound:
                    pass

        if not fp:
            raise NotFound("'%s' could not be found" % uri)

        if uri.endswith(".gpg"):
            fp = Gpg().filter(fp)

        return fp

