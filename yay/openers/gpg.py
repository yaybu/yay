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
import subprocess

from yay.compat import io
from yay.errors import NotFound, NotModified, ParadoxError


class Gpg(object):

    def get_gpg_binary(self):
        # FIXME: Memoize me
        for binary in ('gpg2', 'gpg'):
            for path in os.environ.get('PATH', '/usr/bin').split(":"):
                t = os.path.join(path, binary)
                if os.path.exists(t):
                    return t
        raise NotFound(
            "Unable to decrypt GPG encrypted resource as could not find 'gpg' or 'gpg2'")

    def filter(self, fp):
        data = fp.read()

        # Build an environment for the child process
        # In particular, if GPG_TTY is not set then gpg-agent will not prompt
        # for a passphrase even it is running and correctly configured.
        # GPG_TTY is not required if using seahorse-agent.
        # This is not used on OSX as there is no /proc/self/fd/0
        env = os.environ.copy()
        if not "GPG_TTY" in env:
            if os.path.exists("/proc/self/fd/0"):
                env['GPG_TTY'] = os.readlink('/proc/self/fd/0')

        p = subprocess.Popen(
            [self.get_gpg_binary(), "--use-agent", "--batch", "-d"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate(data)
        if p.returncode != 0:
            msg = "Unable to decrypt resource '%s'" % fp.uri
            if not "GPG_AGENT_INFO" in os.environ:
                msg += "\nGPG Agent not running so your GPG key may not be available"
            raise NotFound(msg)

        stream = io.StringIO(stdout)
        stream.etag = fp.etag
        stream.len = len(stdout)
        stream.uri = fp.uri
        stream.labels = ('secret', )
        return stream
