#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" This is needed to make sure that a server is bound to the aqd service
    before make aquilon runs."""


import socket
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPrebindServer(TestBrokerCommand):

    def testbindntpserver(self):
        self.noouttest(["bind", "server",
            "--hostname", "nyaqd1.ms.com",
            "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifybindntp(self):
        command = "show service --service ntp --instance pa.ny.na"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindaqdserver(self):
        self.noouttest(["bind", "server",
            "--hostname", "nyaqd1.ms.com",
            "--service", "aqd", "--instance", "ny-prod"])

    def testverifybindaqd(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindlemonserver(self):
        self.noouttest(["bind", "server", "--hostname", "nyaqd1.ms.com",
                        "--service", "lemon", "--instance", "ny-prod"])

    def testverifybindlemon(self):
        command = "show service --service lemon --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindsyslogngserver(self):
        self.noouttest(["bind", "server", "--hostname", "nyaqd1.ms.com",
                        "--service", "syslogng", "--instance", "ny-prod"])

    def testverifybindsyslogng(self):
        command = "show service --service syslogng --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindbootserver(self):
        self.noouttest(["bind_server",
                        "--hostname=server9.aqd-unittest.ms.com",
                        "--service=bootserver", "--instance=np.test"])

    def testverifybindbootserver(self):
        command = "show service --service bootserver --instance np.test"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: server9.aqd-unittest.ms.com", command)

    def testbindchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for (s, n) in [(1, 'a'), (2, 'b'), (3, 'c')]:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                server = "server%d.aqd-unittest.ms.com" % s
                instance = "ut.%s" % n
                self.noouttest(["bind", "server", "--hostname", server,
                                "--service", service, "--instance", instance])

    def testbinddns(self):
        self.noouttest(["bind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "dns", "--instance", "utdnsinstance"])
        self.noouttest(["bind", "server",
                        "--hostname", "nyaqd1.ms.com",
                        "--service", "dns", "--instance", "utdnsinstance"])

    def testcatdns(self):
        command = "cat --service dns --instance utdnsinstance"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"servers" = list\(\s*"nyaqd1.ms.com",\s*'
                          r'"unittest02.one-nyp.ms.com"\s*\);',
                          command)
        # The IP address comes from fakebin/dsdb.d, not from the real DNS.
        self.searchoutput(out,
                          '"server_ips" = list\(\s*"10.184.155.249",\s*"%s"\s*\);' %
                          self.net.unknown[0].usable[0],
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrebindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
