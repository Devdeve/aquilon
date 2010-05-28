# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq update branch`."""


import re
import os

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Branch
from aquilon.server.broker import BrokerCommand

VERSION_RE = re.compile(r'^[-_.a-zA-Z0-9]*$')


class CommandUpdateBranch(BrokerCommand):

    required_parameters = ["branch"]

    def render(self, session, logger, branch, comments, compiler_version,
               autosync, noautosync, **arguments):
        dbbranch = Branch.get_unique(session, branch, compel=True)
        if comments:
            dbbranch.comments = comments
        if compiler_version:
            if not VERSION_RE.match(compiler_version):
                raise ArgumentError("Invalid characters in compiler version")
            compiler = self.config.get("panc", "pan_compiler", raw=True) % {
                'version':compiler_version}
            if not os.path.exists(compiler):
                raise ArgumentError("Compiler not found at '%s'" % compiler)
            dbbranch.compiler = compiler
        if noautosync:
            dbbranch.autosync = False
        if autosync:
            dbbranch.autosync = True
        session.add(dbbranch)
        return
