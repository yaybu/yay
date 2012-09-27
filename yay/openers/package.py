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
import subprocess
import pkg_resources
from setuptools.package_index import PackageIndex
from itertools import chain

from yay.errors import NotFound
from .base import IOpener, FileOpener

from tempfile import mkdtemp
import shutil
import urllib2
import urlparse

class TemporaryDirectory(object):

    def __init__(self, suffix="", prefix="tmp", dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        shutil.rmtree(self.name)


class YayPackageIndex(PackageIndex):

    def not_found_in_index(self, requirement):
        self.scan_all()


class PackageOpener(IOpener):

    name = "packages"
    schemes = ("package://", )

    cmd = 'from setuptools.command.easy_install import main; main()'

    DEFAULT_INDEX = "http://pypi.python.org/pypi/"
    _index = None
    _password_mgr = None

    def open(self, uri, etag=None):
        package, uri = uri.lstrip("package://").split("/", 1)
        try:
            __import__(package)
            module = sys.modules[package]
        except ImportError:
            try:
                location = [self._install(package)]
                location.extend(package.split("."))
            except NotFound:
                raise NotFound("Package '%s' could not be imported" % package)
        else:
            location = [os.path.dirname(module.__file__)]
        path = os.path.join(*chain(location, [uri]))
        return FileOpener().open(path, etag)

    @property
    def index(self):
        if not self._index:
            self._index = YayPackageIndex(
                index_url = self.get_setting("index", self.DEFAULT_INDEX),
                python = sys.executable,
                )
        return self._index

    def _install(self, requirement):
        eggdir = os.path.expanduser(self.get_setting("cachedir", "~/.yay/packages"))

        ws  = pkg_resources.working_set
        ws.add_entry(eggdir)

        if not self._password_mgr and self.get_setting("index"):
            mgr = self._password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            parsed = urlparse.urlparse(self.get_setting("index"))
            top_level_url = urlparse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
            mgr.add_password(self.get_setting("realm"), top_level_url, self.get_setting("username"), self.get_setting("password"))

            handler = urllib2.HTTPBasicAuthHandler(mgr)
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)

        def _installer(req):
            if not os.path.exists(eggdir):
                os.makedirs(eggdir)

            self.index.find_packages(req)
            matches = [d for d in self.index[req.key] if d in req]
            if not matches:
                raise NotFound("Could not find package '%s'" % req)

            with TemporaryDirectory(dir=eggdir) as path:
                download = self.index.download(matches[0].location, path)

                command = [sys.executable, "-c", self.cmd, '-ZmqNxd', eggdir]
                command.append(download)
                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()

                if p.returncode != 0:
                    raise NotFound("Unable to install package '%s'" % req)

        parsed = list(pkg_resources.parse_requirements(requirement))
        while 1:
            try:
                ws.resolve(parsed)
            except pkg_resources.DistributionNotFound, err:
                [req] = err
                _installer(req)
            else:
                break

        distro = pkg_resources.get_distribution(requirement)
        return distro.location

