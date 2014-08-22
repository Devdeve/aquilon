#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the unbind cluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUnbindCluster(TestBrokerCommand):

    def testfailservicemissingcluster(self):
        command = ["unbind_cluster", "--cluster", "cluster-does-not-exist",
                   "--service=esx_management_server"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailservicenotbound(self):
        command = ["unbind_cluster", "--cluster", "utecl1", "--service=utsvc"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service utsvc is not bound to ESX cluster utecl1.",
                         command)

    def testfailunbindrequiredservice(self):
        command = ["show_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)

        command = ["unbind_cluster", "--cluster=utecl1",
                   "--service=esx_management_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot remove cluster service instance binding for "
                         "esx cluster aligned service esx_management_server.",
                         command)

    def testunbindservice(self):
        # This also tests binding a non-aligned service...
        # not sure if there should be a test of running make against a
        # cluster (or a cluster with hosts) while bound to such a service...
        command = ["bind_cluster", "--cluster=utecl4",
                   "--service=utsvc", "--instance=utsi1"]
        (out, err) = self.successtest(command)

        command = ["unbind_cluster", "--cluster=utecl4", "--service=utsvc"]
        out = self.commandtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
