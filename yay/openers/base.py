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
import base64

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

    def __init__(self, factory=None):
        self.factory = factory

    def get_setting(self, key, default=None):
        if self.factory:
            self.factory.config.setdefault(self.name, {})
            return self.factory.config[self.name].get(key, default)
        return default

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
        p = urlparse.urlparse(uri)
        netloc = p.hostname
        if p.port:
            netloc += ":" + p.port
        uri = urlparse.urlunparse((p.scheme, netloc, p[2], p[3], p[4], p[5]))

        req = urllib2.Request(uri)

        if p.username and p.password:
            header = base64.encodestring("%s:%s" % (p.username, p.password))
            req.add_header("Authorization", "Basic " + header)

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
            import yaml
            data = self.get_setting(uri)
            if not data:
                raise NotFound("Memory cell '%s' does not exist" % uri)
            data = yaml.dump(data, default_flow_style=False)

        fp = StringIO.StringIO(data)
        fp.len = len(data)

        new_etag = etag_stream(StringIO.StringIO(data))
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


class Gpg(object):

    def filter(self, fp):
        data = fp.read()

        # Build an environment for the child process
        # In particular, if GPG_TTY is not set then gpg-agent will not prompt
        # for a passphrase even it is running and correctly configured.
        # GPG_TTY is not required if using seahorse-agent.
        env = os.environ.copy()
        if not "GPG_TTY" in env:
            env['GPG_TTY'] = os.readlink('/proc/self/fd/0')

        p = subprocess.Popen(["gpg", "--batch", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate(data)
        if p.returncode != 0:
            msg = "Unable to decrypt resource '%s'" % fp.uri
            if not "GPG_AGENT_INFO" in os.environ:
                msg += "\nGPG Agent not running so your GPG key may not be available"
            raise NotFound(msg)
        stream = StringIO.StringIO(stdout)
        stream.etag = fp.etag
        stream.len = len(stdout)
        stream.uri = fp.uri
        stream.secret = True
        return stream


class Openers(object):

    def __init__(self, searchpath=None, config=None):
        self.searchpath = searchpath or []
        self.config = config or {}

        self.openers = []
        for cls in IOpener.__subclasses__():
            self.openers.append(cls(self))

    def update(self, config):
        def _merge(self, a, b):
            out = {}
            for k, v in b.items():
                if k in a:
                    if isinstance(a[k], dict) and isinstance(v, dict):
                        out[k] = _merge(a[k], v)
                        continue
                out[k] = v
            return out
        self.config = _merge(self.config, config)

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

