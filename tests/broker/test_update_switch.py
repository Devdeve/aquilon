#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the update switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from switchtest import VerifySwitchMixin


class TestUpdateSwitch(TestBrokerCommand, VerifySwitchMixin):

    def testfailnomodel(self):
        command = ["update", "switch", "--vendor", "generic",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model uttorswitch, vendor generic, "
                         "machine_type switch not found.",
                         command)

    def testupdateut3gd1r04(self):
        newip = self.net.tor_net[6].usable[1]
        self.dsdb_expect_update("ut3gd1r04.aqd-unittest.ms.com", "xge49", newip,
                                comments="Some new switch comments")
        command = ["update", "switch", "--type", "bor",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--ip", newip, "--model", "uttorswitch",
                   "--comments", "Some new switch comments"]
        self.noouttest(command)
        self.dsdb_verify()

    def testupdatebadip(self):
        ip = self.net.tor_net[12].usable[0]
        command = ["update", "switch", "--ip", ip,
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by on-board admin "
                         "interface xge of switch "
                         "ut3gd1r01.aqd-unittest.ms.com." % ip,
                         command)

    def testupdatemisc(self):
        command = ["update", "switch",
                   "--switch", "ut3gd1r05.aqd-unittest.ms.com",
                   "--rack", "ut4", "--model", "uttorswitch",
                   "--vendor", "hp", "--serial", "SNgd1r05_new"]
        self.noouttest(command)

    def testaddinterface(self):
        ip = self.net.tor_net[8].usable[0]
        mac = self.net.tor_net[8].usable[1].mac
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", "xge", mac=mac)
        self.dsdb_expect_rename("ut3gd1r06.aqd-unittest.ms.com", iface="xge",
                                new_iface="xge49")
        command = ["add_interface", "--switch=ut3gd1r06.aqd-unittest.ms.com",
                   "--interface=xge49", "--mac", mac]
        self.noouttest(command)
        (out, cmd) = self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com",
                                       "generic", "temp_switch", "ut3", "a", "3",
                                       switch_type='tor',
                                       ip=ip, mac=mac, interface="xge49")
        # Verify that the auto-created dummy interface is gone
        self.matchclean(out, "Interface: xge ", command)
        self.dsdb_verify()

    def testupdatewithinterface(self):
        newip = self.net.tor_net[8].usable[1]
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", "xge49", newip)
        command = ["update", "switch",
                   "--switch", "ut3gd1r06.aqd-unittest.ms.com",
                   "--ip", newip]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyupdatewithoutinterface(self):
        self.verifyswitch("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[6].usable[1],
                          mac=self.net.tor_net[6].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

    def testverifyupdatemisc(self):
        self.verifyswitch("ut3gd1r05.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut4", "a", "4", "SNgd1r05_new", switch_type='tor',
                          ip=self.net.tor_net[7].usable[0], interface="xge49")

    def testverifyupdatewithinterface(self):
        self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[8].usable[1],
                          mac=self.net.tor_net[8].usable[1].mac,
                          interface="xge49")

    def testverifydsdbrollback(self):
        self.verifyswitch("ut3gd1r07.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[9].usable[0])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
