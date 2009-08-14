#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Module for testing the unbind esx cluster command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUnbindESXCluster(TestBrokerCommand):

    def testfailunbindevh1(self):
        command = ["unbind_esx_cluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host 'evh1.aqd-unittest.ms.com' is bound to "
                         "esx cluster 'utecl2', not ESX cluster 'utecl1'.",
                         command)

    def testunbindevh1(self):
        self.noouttest(["unbind_esx_cluster",
                        "--hostname", "evh1.aqd-unittest.ms.com",
                        "--cluster", "utecl2"])

    def testunbindhosts(self):
        for i in range(2, 5):
            self.noouttest(["unbind_esx_cluster",
                            "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                            "--cluster", "utecl1"])

    def testverifyunbindhosts(self):
        for i in range(1, 5):
            command = "show host --hostname evh%s.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Hostname: evh%s.aqd-unittest.ms.com" % i,
                             command)
            self.matchclean(out, "Member of esx cluster", command)

    def testfailmissingcluster(self):
        command = ["unbind_esx_cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "ESX Cluster 'cluster-does-not-exist' not found.",
                         command)

    def testfailunboundcluster(self):
        command = ["unbind_esx_cluster",
                   "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "not bound to a cluster", command)

    def testfailservicemissingcluster(self):
        command = ["unbind_esx_cluster", "--cluster", "cluster-does-not-exist",
                   "--service=esx_management", "--instance=ut.a"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "esx cluster 'cluster-does-not-exist' not found.",
                         command)

    def testfailservicenotbound(self):
        command = ["unbind_esx_cluster", "--cluster", "utecl1",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Service utsvc instance utsi1 is not bound to "
                         "esx cluster utecl1",
                         command)

    def testfailunbindrequiredservice(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service esx_management '
                              r'Instance (\S+)',
                              command)
        instance = m.group(1)

        command = ["unbind_esx_cluster", "--cluster=utecl1",
                   "--service=esx_management", "--instance=%s" % instance]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot remove cluster service instance binding for "
                         "esx cluster aligned service esx_management.",
                         command)

    def testunbindservice(self):
        # This also tests binding a non-aligned service...
        # not sure if there should be a test of running make against a
        # cluster (or a cluster with hosts) while bound to such a service...
        command = ["bind_esx_cluster", "--cluster=utecl4",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.commandtest(command)

        command = ["unbind_esx_cluster", "--cluster=utecl4",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.commandtest(command)

    # FIXME: Also test plenary files.


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
