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
import hashlib
import base64
import itertools

from yay.compat import io, request, parse, zip_longest
from yay.errors import NotFound, NotModified, ParadoxError
from .gpg import Gpg

try:
    unicode = unicode
except NameError:  # pragma: no cover
    unicode = str


def etag_stream(fp):
    s = hashlib.sha1()
    while True:
        block = fp.read(8192)
        if not block:
            break
        # FIXME: should unicode even get here?
        if isinstance(block, unicode):
            block = block.encode("utf-8")
        s.update(block)
    return s.hexdigest()


class IOpener(object):

    def __init__(self, factory=None):
        self.factory = factory

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

    name = "files"
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

            @property
            def labels(self):
                return ()

        fp = open(uri, "rb")
        new_etag = etag_stream(fp)

        if etag and etag == new_etag:
            fp.close()
            raise NotModified("File '%s' not modified" % uri)

        fp.seek(0)
        f = File(fp)
        f.etag = new_etag
        f.uri = uri
        return f


class HomeOpener(IOpener):

    name = "home"
    schemes = ("home://", )

    def open(self, uri, etag=None):
        uri = os.path.expanduser("~/" + uri.lstrip("home://"))
        return FileOpener(self.factory).open(uri, etag)


class UrlOpener(IOpener):

    name = "urls"
    schemes = ("http://", "https://")

    def open(self, uri, etag=None):
        p = parse.urlparse(uri)
        netloc = p.hostname
        if p.port:
            netloc += ":" + p.port
        uri = parse.urlunparse((p.scheme, netloc, p[2], p[3], p[4], p[5]))

        req = request.Request(uri)

        if p.username and p.password:
            header = base64.encodestring("%s:%s" % (p.username, p.password))
            req.add_header("Authorization", "Basic " + header)

        if etag:
            req.add_header("If-None-Match", etag)

        try:
            fp = request.urlopen(req)

        except request.URLError as exc:
            raise NotFound("URL '%s' not found (URLError)" % uri)

        except request.HTTPError as exc:
            if exc.code == 304:
                raise NotModified("URL '%s' has not been modified" % uri)
            raise NotFound(
                "URL '%s' could not be found (HTTP response %s)" % (uri, exc.code))

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

            @property
            def labels(self):
                return ()

            uri = uri

        return Resource(fp)


class MemOpener(IOpener):

    """
    This is purely a testing stub.

    It has a class-shared dictionary called 'data', where keys are uris and
    values are data to return as a StringIO when open() is called. This means
    test cases can exercise the yay extends machinery without the need to create
    temporary files
    """

    name = "memory"
    schemes = ("mem://", )
    data = {}

    @classmethod
    def _simplify_uri(cls, uri):
        assert uri.startswith("mem://")
        return uri[6:]

    def open(self, uri, etag=None):
        uri = self._simplify_uri(uri)

        try:
            data = self.data[uri]
        except KeyError:
            raise NotFound("Memory cell '%s' does not exist" % uri)

        fp = io.StringIO(data)
        fp.len = len(data)
        fp.labels = ()

        new_etag = etag_stream(io.StringIO(data))
        if etag and new_etag == etag:
            raise NotModified("Memory cell '%s' hasn't changed" % uri)
        fp.etag = new_etag
        fp.uri = uri

        return fp

    @classmethod
    def add(cls, uri, data):
        cls.data[cls._simplify_uri(uri)] = data

    @classmethod
    def reset(cls):
        cls.data = {}


class Openers(object):

    def __init__(self, searchpath=None):
        self.searchpath = searchpath or []

        self.openers = []
        for cls in IOpener.__subclasses__():
            self.openers.append(cls(self))

    def _scheme(self, uri):
        parsed = parse.urlparse(uri)
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

        return FileOpener(self).open(uri, etag)

    def open(self, uri, etag=None):
        fp = None

        if uri.startswith("/"):
            fp = FileOpener(self).open(uri, etag)
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


class SearchpathFromGraph(object):

    """
    SearchpathFromGraph is an adaptor for basing the search path on an
    expression in the Graph::

        class CustomRoot(ast.Root):

            def setup_openers(self):
                #Add a yay.searchpath variable to the graph
                self.add({"yay": {"searchpath": self.searchpath or []}})

                #Allow nodes in the graph to extend the searchpath
                self.openers = Openers(searchpath=SearchpathFromGraph(self.yay.searchpath))

    As far as the openers code is concerned, the searchpath is a simple list.
    However, if a user changes the searchpath in a way that violates causality
    the appropriate exception is raised.
    """

    def __init__(self, expression):
        self.expression = expression
        self._previous = []
        self._iterating = False

    def _iterate_over_expression(self):
        marker = object()
        previous = list(self._previous)
        current = self.expression.as_iterable()

        for p, c in zip_longest(previous, current, fillvalue=marker):
            if p != marker:
                if p != c:
                    raise ParadoxError(
                        "Searchpath changed after we started depending on it")
            else:
                self._previous.append(c)
            yield c

    def __iter__(self):
        if not self._iterating:
            self._iterating = True
            gen = self._iterate_over_expression()
            self._iterating = False
            try:
                while True:
                    self._iterating = True
                    val = next(gen)
                    self._iterating = False
                    yield val
            except StopIteration:
                self._iterating = False
                return
        for val in self._previous:
            yield val
