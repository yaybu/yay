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
from itertools import chain

from yay.errors import NotFound
from .base import IOpener, FileOpener

class PackageOpener(IOpener):

    schemes = ("package://", )

    cmd = 'from setuptools.command.easy_install import main; main()'
    python = sys.executable
    eggdir = os.path.expanduser("~/.yay/packages")

    def open(self, uri, etag=None):
        package, uri = uri.lstrip("package://").split("/", 1)
        try:
            location = [self._install(package)]
            location.extend(package.split("."))
        except ImportError:
            # This old code path only exists for the old case where you might
            # have specified a module within a package to import
            try:
                __import__(package)
                module = sys.modules[package]
            except ImportError:
                raise NotFound("Package '%s' could not be imported" % package)
            location = [os.path.dirname(module.__file__)]
        path = os.path.join(*chain(location, [uri]))
        return FileOpener().open(path, etag)

    def _install(self, requirement):
        ws  = pkg_resources.working_set
        ws.add_entry(self.eggdir)

        def _installer(requirement):
            if not os.path.exists(self.eggdir):
                os.makedirs(self.eggdir)
        
            # The base easy_install command
            command = [self.python, "-c", self.cmd, '-mqNxd', self.eggdir]

            # User can set up an alternative PyPI index
            # if self.index:
            #     command.extend(["-i", self.index])

            # Actually add requirements
            command.append(str(requirement))

            # Actually run the command
            result = subprocess.Popen(command).wait()

            if result != 0:
                raise ImportError("Unable to automatically fetch package '%s' % requirement")

            # Recursively resolve any dependencies of this package
            ws.resolve([requirement], installer=_installer)
            return pkg_resources.get_distribution(requirement)

        parsed = list(pkg_resources.parse_requirements(requirement))
        ws.resolve(parsed, installer=_installer)

        distro = pkg_resources.get_distribution(requirement)
        return distro.location

