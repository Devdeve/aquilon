#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Module for testing the get domain command."""

import os
import unittest
from subprocess import Popen

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestGet(TestBrokerCommand):

    def testclearchangetest1domain(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest1")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def testclearchangetest2domain(self):
        p = Popen(("/bin/rm", "-rf",
                   os.path.join(self.sandboxdir, "changetest2")),
                  stdout=1, stderr=2)
        rc = p.wait()

    def testgetchangetest1domain(self):
        (out, err) = self.successtest(["get", "--sandbox", "changetest1"])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "changetest1")))

    def testgetchangetest2domain(self):
        user = self.config.get("unittest", "user")
        (out, err) = self.successtest(["get",
                                       "--sandbox=%s/changetest2" % user])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "changetest2")))

    def testgetutsandbox(self):
        # This one was added with --noget
        (out, err) = self.successtest(["get", "--sandbox", "utsandbox"])
        self.failUnless(os.path.exists(os.path.join(self.sandboxdir,
                                                    "utsandbox")))

    def testgetbaduser(self):
        command = ["get",
                   "--sandbox", "user-does-not-exist/badbranch"]
        out = self.badrequesttest(command)
        user = self.config.get("unittest", "user")
        self.matchoutput(out,
                         "User '%s' cannot add or get a sandbox on "
                         "behalf of 'user-does-not-exist'." % user,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGet)
    unittest.TextTestRunner(verbosity=2).run(suite)
