#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add machine command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from machinetest import MachineTestMixin
from networktest import DummyIP


class TestAddMachine(MachineTestMixin, TestBrokerCommand):
    def test_100_add_ut3c5n10(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n10",
                        "--chassis", "ut3c5", "--slot", 10,
                        "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon_2660", "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "99C5553",
                        "--comments", "Some machine comments"])

    def test_101_update_ut3c5n10_ip(self):
        command = ["update", "machine", "--machine", "ut3c5n10",
                   "--ip", self.net["unknown0"].usable[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Machine ut3c5n10 does not have a primary name.",
                         command)

    def test_105_show_ut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Chassis: ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 10", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)
        self.matchoutput(out, "Comments: Some machine comments", command)
        self.matchclean(out, "Primary Name:", command)

    def test_105_verify_del_model(self):
        # This should be in test_del_model.py but when that is run there are no
        # more machines defined...
        command = "del model --model hs21-8853l5u --vendor ibm"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model ibm/hs21-8853l5u is still in use and "
                         "cannot be deleted.", command)

    def test_105_cat_ut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "99C5553";', command)
        # DNS maps:
        # - aqd-unittest.ms.com comes from rack ut3
        # - utroom1 also has aqd-unittest.ms.com mapped _after_ td1 and td2,
        #   but the rack mapping is more specific, so aqd-unittest.ms.com
        #   remains at the beginning
        # - new-york.ms.com comes from the campus
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = list\(\s*'
                          r'"aqd-unittest.ms.com",\s*'
                          r'"td1.aqd-unittest.ms.com",\s*'
                          r'"td2.aqd-unittest.ms.com",\s*'
                          r'"new-york.ms.com"\s*\);',
                          command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)
        self.matchoutput(out, '"chassis" = "ut3c5.aqd-unittest.ms.com";', command)
        self.matchoutput(out, '"slot" = 10;', command)

    # Used for Zebra tests
    def test_110_add_ut3c5n2(self):
        self.create_machine_hs21("ut3c5n2", chassis="ut3c5", slot=2,
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[0].mac,
                                 eth0_vendor="intel", eth0_model="e1000",
                                 eth1_mac=self.net["zebra_eth1"].usable[0].mac,
                                 eth1_model="e1000")

    # Used for bonding tests
    def test_111_add_ut3c5n3(self):
        self.create_machine_hs21("ut3c5n3", chassis="ut3c5", slot=3,
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[1].mac,
                                 eth1_mac=self.net["zebra_eth1"].usable[1].mac)

    # Used for bridge tests
    def test_112_add_ut3c5n4(self):
        self.create_machine_hs21("ut3c5n4", chassis="ut3c5", slot=4,
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["zebra_eth0"].usable[2].mac,
                                 eth1_mac=self.net["zebra_eth1"].usable[2].mac)

    # Used for house-of-cards location testing
    def test_120_add_jack(self):
        self.noouttest(["add", "machine", "--machine", "jack",
                        "--rack", "cards1", "--model", "utrackmount"])

    # Used for filer - a fake machine for now
    def test_125_add_filer(self):
        self.noouttest(["add", "machine", "--machine", "filer1",
                        "--rack", "ut3", "--model", "utrackmount"])

    # Used for VPLS network tests
    def test_130_add_ut3c5n5(self):
        self.create_machine_hs21("ut3c5n5", chassis="ut3c5", slot=5,
                                 eth0_mac=self.net["vpls"].usable[1].mac)

    # Test normalization
    def test_131_add_np3c5n5(self):
        self.create_machine_hs21("np3C5N5", chassis="np3c5", slot=5,
                                 eth0_mac=self.net["vpls"].usable[2].mac)

    def test_135_verify_normalization(self):
        command = "show machine --machine NP3c5N5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: np3c5n5", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: np3c5.one-nyp.ms.com", command)
        self.matchoutput(out, "Slot: 5", command)

        command = "show machine --machine np3c5n5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: np3c5n5", command)
        self.matchoutput(out, "Model Type: blade", command)

    # Used for testing notifications
    def test_140_add_ut3c5n6(self):
        self.create_machine_hs21("ut3c5n6", chassis="ut3c5", slot=6,
                                 eth0_mac=self.net["unknown0"].usable[19].mac)

    # Network environment testing
    def test_141_add_ut3c5n7(self):
        net = self.net["unknown0"]
        self.create_machine_hs21("ut3c5n7", chassis="ut3c5", slot=7,
                                 interfaces=["eth0", "eth1", "eth2"],
                                 eth0_mac=net.usable[20].mac,
                                 eth1_mac=net.usable[21].mac,
                                 eth2_mac=net.usable[22].mac)

    # Network environment testing
    def test_142_add_ut3c5n8(self):
        self.create_machine_hs21("ut3c5n8", chassis="ut3c5", slot=8,
                                 interfaces=["eth0", "eth1"],
                                 eth0_mac=self.net["unknown0"].usable[23].mac,
                                 eth1_mac=self.net["routing1"].usable[0].mac)

    def test_143_add_ut3c1n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n3",
                        "--chassis", "ut3c1.aqd-unittest.ms.com", "--slot", "3",
                        "--model", "hs21-8853l5u", "--cpucount", "2",
                        "--cpuvendor", "intel", "--cpuname", "xeon_2660",
                        "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "KPDZ406"])

    def test_145_show_slot(self):
        command = "search machine --slot 3 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_145_show_chassis_slot(self):
        command = "search machine --chassis ut3c1.aqd-unittest.ms.com --slot 3 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_145_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def test_145_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"rack/name" = "ut3";', command)
        self.matchoutput(out, '"rack/row" = "a";', command)
        self.matchoutput(out, '"rack/column" = "3";', command)
        self.matchoutput(out, '"rack/room" = "utroom1";', command)
        self.matchoutput(out, '"sysloc/building" = "ut";', command)
        self.matchoutput(out, '"sysloc/city" = "ny";', command)
        self.matchoutput(out, '"sysloc/continent" = "na";', command)
        self.matchoutput(out,
                         '"chassis" = "ut3c1.aqd-unittest.ms.com";',
                         command)
        self.matchoutput(out, '"slot" = 3;', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ406";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    def test_150_add_ut3c1n4(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n4",
                        "--chassis", "ut3c1", "--slot", 4,
                        "--model", "hs21-8853l5u", "--serial", "KPDZ407"])

    def test_155_show_ut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n4", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ407", command)

    def test_155_cat_ut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ407";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    def test_160_add_cciss_machine(self):
        self.create_machine("ut3c1n8", "utccissmodel", rack="ut3",
                            eth0_mac=self.net["unknown0"].usable[18].mac)

    def test_165_show_cciss_machine(self):
        command = "show machine --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n8", command)
        self.matchoutput(out, "Model Type: rackmount", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: utccissmodel", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 2", command)
        self.matchoutput(out, "Memory: 49152 MB", command)
        self.matchoutput(out, "Disk: c0d0 466 GB cciss (local) [boot]", command)

    def test_165_cat_cciss_machine(self):
        command = "cat --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/hp/utccissmodel" };',
                         command)
        self.matchoutput(out,
                         '"harddisks/{cciss/c0d0}" = '
                         'create("hardware/harddisk/generic/cciss",',
                         command)
        self.matchoutput(out,
                         '"capacity", 466*GB',
                         command)

    def test_170_add_ut3c1n9(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n9",
                        "--model", "hs21-8853l5u",
                        "--chassis", "ut3c1", "--slot", 9])

    def test_171_addut3s01p2(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p2",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def test_175_show_ut3s01p2(self):
        command = "show machine --machine ut3s01p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p2", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    # When doing an end-to-end test, these two entries should be
    # created as part of a sweep of a Dell rack.  They represent
    # two mac addresses seen on the same port, only one of which
    # is actually a host.  The other is a management interface.
    def test_180_add_ut3s01p1a(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1a",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def test_181_show_ut3s01p1a(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p1a", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    def test_182_add_ut3s01p1b(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1b",
                        "--rack", "ut3", "--model", "poweredge_6650"])

    def test_183_show_ut3s01p1b(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p1b", command)
        self.matchoutput(out, "Model Type: rackmount", command)

    # When doing an end-to-end test, these entries should be
    # created as part of a sweep of a Verari rack
    # (ut01ga1s02.aqd-unittest.ms.com).
    def test_190_add_verari_ut8(self):
        net = self.net["tor_net_0"]
        for port in range(1, 6):
            machine = "ut8s02p%d" % port
            self.create_machine(machine, "vb1205xm", rack="ut8",
                                eth0_mac=net.usable[port].mac)

    def test_191_add_ut_no_rack(self):
        # A machine that's not in a rack
        self.noouttest(["add", "machine", "--machine", "utnorack",
                        "--desk", "utdesk1", "--model", "poweredge_6650"])

    def test_193_add_f5test(self):
        ip = DummyIP(self.net["f5test"].ip)
        self.create_machine("f5test", "f5_model", rack="ut3", eth0_mac=ip.mac)

    def test_200_reject_qualified_name(self):
        command = ["add", "machine", "--machine", "qualified.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Illegal hardware label format 'qualified.ms.com'.",
                         command)

    # Testing that add machine does not allow a tor_switch....
    def test_210_reject_switch(self):
        command = ["add", "machine", "--machine", "ut3gd1r02",
                   "--rack", "ut3", "--model", "uttorswitch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot add machines of type switch",
                         command)

    def test_215_verify_reject_switch(self):
        command = "show machine --machine ut3gd2r01"
        out = self.notfoundtest(command.split(" "))

    # Testing that an invalid cpu returns an error (not an internal error)...
    # (There should be no cpu with speed==2 in the database)
    def test_220_reject_bad_cpuspeed(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3c1n5",
                             "--rack", "ut3", "--model", "hs21-8853l5u",
                             "--cpucount", "2", "--cpuvendor", "intel",
                             "--cpuname", "xeon_2660", "--cpuspeed", "2",
                             "--memory", "8192", "--serial", "KPDZ406"])

    def test_225_verify_reject_bad_cpuspeed(self):
        command = "show machine --machine ut3c1n5"
        out = self.notfoundtest(command.split(" "))

    def test_230_reject_missing_memory(self):
        command = ["add", "machine", "--machine", "ut3c1n6",
                   "--rack", "ut3", "--model", "utblade", "--cpucount", "2",
                   "--cpuvendor", "intel", "--cpuname", "xeon_2500",
                   "--cpuspeed", "2500", "--serial", "AAAAAAA"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "does not have machine specification defaults, please specify --memory",
                         command)

    def test_235_verify_reject_missing_memory(self):
        command = "show machine --machine ut3c1n6"
        out = self.notfoundtest(command.split(" "))

    def test_240_reject_missing_model(self):
        command = ["add", "machine", "--machine", "ut3c1n7", "--rack", "ut3",
                   "--model", "utblade", "--serial", "BBBBBBB"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "does not have machine specification defaults",
                         command)

    def test_245_verify_reject_missing_model(self):
        command = "show machine --machine ut3c1n7"
        out = self.notfoundtest(command.split(" "))

    def test_250_reject_machine_uri(self):
        command = ["add", "machine", "--machine", "ut3c1n10",
                   "--rack", "ut3", "--model", "hs21-8853l5u",
                   "--uri", "file:///somepath/to/ovf"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "URI can be specified only for virtual "
                         "appliances and the model's type is blade",
                         command)

    def test_255_verify_reject_machine_uri(self):
        command = "show machine --machine ut3c1n10"
        out = self.notfoundtest(command.split(" "))

    # FIXME: Missing a test for adding a macihne to a chassis where the
    # fqdn given for the chassis isn't *actually* a chassis.
    # FIXME: Missing a test for chassis without a slot.  (May not be possible
    # with the aq client.)
    # FIXME: Missing a test for a slot without a chassis.  (May not be possible
    # with the aq client.)
    # FIXME: Add a test where the machine trying to be created already exists.

    # Note: More regression tests are in the test_add_virtual_hardware module.


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
