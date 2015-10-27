#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the make command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestMake(TestBrokerCommand):

    # network based service mappings
    def testmakeafsbynet_1_checkloc(self):
        # Must by issued before map service.
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: afs Instance: q.ny.ms.com",
                         command)

    def testmakeafsbynet_2_mapservice(self):
        ip = self.net["netsvcmap"].subnet()[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "afs", "--instance", "afs-by-net"])
        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "afs", "--instance", "afs-by-net2"])

    def testmakeafsbynet_3_verifymapservice(self):
        ip = self.net["netsvcmap"].subnet()[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: afs "
                         "Instance: afs-by-net Map: Network netsvcmap",
                         command)

    def testmakeafsbynet_3_verifymapservice_proto(self):
        ip = self.net["netsvcmap"].subnet()[0].ip

        command = ["show_map", "--service=afs", "--instance=afs-by-net",
                   "--networkip=%s" % ip, "--format=proto"]
        service_map = self.protobuftest(command, expect=1)[0]
        self.assertEqual(service_map.network.ip, str(ip))
        self.assertEqual(service_map.network.cidr, 27)
        self.assertEqual(service_map.network.type, "unknown")
        self.assertEqual(service_map.network.env_name, 'internal')
        self.assertEqual(service_map.service.name, 'afs')
        self.assertEqual(service_map.service.serviceinstances[0].name,
                         'afs-by-net')

    def testmakeafsbynet_4_make(self):
        command = ["make", "--hostname", "afs-by-net.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname afs-by-net.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        # This can be either afs-by-net or afs-by-net2
        self.matchoutput(out,
                         "Uses Service: afs Instance: afs-by-net",
                         command)

    def testmakeafsbynet_5_mapconflicts(self):
        ip = self.net["netsvcmap"].subnet()[0].ip

        command = ["map", "service", "--networkip", ip,
                   "--service", "afs", "--instance", "afs-by-net",
                   "--building", "whatever"]
        out = self.badoptiontest(command)

        self.matchoutput(out,
                         "Please provide exactly one of the required options!",
                         command)

    # network / personality based service mappings

    def testmakenetmappers_1_maplocsvc_nopers(self):
        """Maps a location based service map just to be overridden by a location
        based personality service map"""
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "netmap", "--instance", "q.ny.ms.com"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: netmap Instance: q.ny.ms.com",
                         command)

    def testmakenetmappers_2_maplocsvc_pers(self):
        """Maps a location based personality service map to be overridden by a
        network based personality service map"""
        self.noouttest(["map", "service", "--building", "ut", "--personality",
                        "eaitools", "--archetype", "aquilon",
                        "--service", "netmap", "--instance", "p-q.ny.ms.com"])

        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: netmap Instance: p-q.ny.ms.com",
                         command)

    def testmakenetmappers_3_mapservice(self):
        ip = self.net["netperssvcmap"].subnet()[0].ip

        self.noouttest(["map", "service", "--networkip", ip,
                        "--service", "netmap", "--instance", "netmap-pers",
                        "--personality", "eaitools",
                        "--archetype", "aquilon"])

    def testmakenetmappers_4_verifymapservice(self):
        ip = self.net["netperssvcmap"].subnet()[0].ip

        command = ["show_map", "--service=netmap", "--instance=netmap-pers",
                   "--networkip=%s" % ip, "--personality", "eaitools",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: eaitools "
                         "Service: netmap "
                         "Instance: netmap-pers Map: Network netperssvcmap",
                         command)

    def testmakenetmappers_5_verifymapservice_proto(self):
        ip = self.net["netperssvcmap"].subnet()[0].ip

        command = ["show_map", "--service=netmap", "--instance=netmap-pers",
                   "--networkip=%s" % ip, "--personality", "eaitools",
                   "--archetype", "aquilon", "--format=proto"]
        service_map = self.protobuftest(command, expect=1)[0]
        self.assertEqual(service_map.network.ip, str(ip))
        self.assertEqual(service_map.network.cidr, 27)
        self.assertEqual(service_map.network.type, "unknown")
        self.assertEqual(service_map.network.env_name, 'internal')
        self.assertEqual(service_map.service.name, 'netmap')
        self.assertEqual(service_map.service.serviceinstances[0].name,
                         'netmap-pers')
        self.assertEqual(service_map.personality.name, 'eaitools')
        self.assertEqual(service_map.personality.archetype.name, 'aquilon')

    def testmakenetmappers_6_make(self):
        command = ["make", "--hostname", "netmap-pers.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)

        command = "show host --hostname netmap-pers.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: netmap Instance: netmap-pers",
                         command)

    def testmakevmhosts(self):
        for i in range(1, 6):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i,
                       "--osname", "esxi", "--osversion", "5.0.0"]
            (out, err) = self.successtest(command)
            self.matchclean(err, "removing binding", command)

            self.assertTrue(os.path.exists(os.path.join(
                self.config.get("broker", "profilesdir"),
                "evh1.aqd-unittest.ms.com%s" % self.xml_suffix)))

            self.assertTrue(os.path.exists(
                self.build_profile_name("evh1.aqd-unittest.ms.com",
                                        domain="unittest")))

            servicedir = os.path.join(self.config.get("broker", "plenarydir"),
                                      "servicedata")
            results = self.grepcommand(["-rl", "evh%s.aqd-unittest.ms.com" % i,
                                        servicedir])
            self.assertTrue(results, "No service plenary data that includes"
                            "evh%s.aqd-unittest.ms.com" % i)

    def testmake10gighosts(self):
        for i in range(51, 75):
            command = ["make", "--hostname", "evh%s.aqd-unittest.ms.com" % i]
            (out, err) = self.successtest(command)

    def testmakeutmc9(self):
        command = ["make", "--hostname", "evh82.aqd-unittest.ms.com"]
        self.statustest(command)

        command = ["show", "host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Uses Service: vcenter Instance: ut", command)

    def testmakeccisshost(self):
        command = ["make", "--hostname=unittest18.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def testmakezebra(self):
        command = ["make", "--hostname", "unittest20.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def testverifyunittest20(self):
        eth0_ip = self.net["zebra_eth0"].usable[0]
        eth0_broadcast = self.net["zebra_eth0"].broadcast
        eth0_netmask = self.net["zebra_eth0"].netmask
        eth0_gateway = self.net["zebra_eth0"].gateway

        eth1_ip = self.net["zebra_eth1"].usable[0]
        eth1_broadcast = self.net["zebra_eth1"].broadcast
        eth1_netmask = self.net["zebra_eth1"].netmask
        eth1_gateway = self.net["zebra_eth1"].gateway
        eth1_1_ip = self.net["zebra_eth1"].usable[3]

        hostname_ip = self.net["zebra_vip"].usable[2]
        zebra2_ip = self.net["zebra_vip"].usable[1]
        zebra3_ip = self.net["zebra_vip"].usable[0]

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template hostdata/unittest20.aqd-unittest.ms.com;",
                         command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/hostname/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra2/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/zebra3/config"\)\);',
                          command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s",\s*"%s"\s*\),\s*'
                          r'"eth1", list\(\s*"%s",\s*"%s"\s*\)\s*'
                          r'\);' % (self.net["zebra_eth0"][1],
                                    self.net["zebra_eth0"][2],
                                    self.net["zebra_eth1"][1],
                                    self.net["zebra_eth1"][2]),
                          command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e0.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (eth0_broadcast, eth0_gateway, eth0_ip, eth0_netmask),
                          command)
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"aliases", nlist\(\s*'
                          r'"e1", nlist\(\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e1-1.aqd-unittest.ms.com",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s"\s*\)\s*\),\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest20-e1.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (eth1_broadcast, eth1_1_ip, eth1_netmask,
                           eth1_broadcast, eth1_gateway, eth1_ip, eth1_netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         eth0_gateway, command)

        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";',
                         command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";',
                         command)
        self.matchclean(out, '"/metadata/template/branch/author"', command)

        command = ["cat", "--service_address", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "hostname";', command)
        self.matchoutput(out, '"ip" = "%s";' % hostname_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "unittest20.aqd-unittest.ms.com";',
                         command)

        command = ["cat", "--service_address", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "zebra2";', command)
        self.matchoutput(out, '"ip" = "%s";' % zebra2_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "zebra2.aqd-unittest.ms.com";',
                         command)

        command = ["cat", "--service_address", "zebra3",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "zebra3";', command)
        self.matchoutput(out, '"ip" = "%s";' % zebra3_ip, command)
        self.searchoutput(out,
                          r'"interfaces" = list\(\s*"eth0",\s*"eth1"\s*\);',
                          command)
        self.matchoutput(out, '"fqdn" = "zebra3.aqd-unittest.ms.com";',
                         command)

    def testmakeunittest21(self):
        command = ["make", "--hostname", "unittest21.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def testverifyunittest21(self):
        net = self.net["zebra_eth0"]
        command = ["cat", "--hostname", "unittest21.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         net.gateway, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"bond0", list\(\s*'
                          r'"%s",\s*"%s"\s*\)\s*\);' % (net[1], net[2]),
                          command)

    def testmakeunittest23(self):
        command = ["make", "--hostname", "unittest23.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def testverifyunittest23(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest23.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["vpls"]
        ip = net.usable[1]
        router = net[1]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest23.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\);' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def testmakeunittest24(self):
        command = ["make", "--hostname", "unittest24.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "2/2 compiled", command)

    def testverifyunittest24(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest24.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["vpls"]
        ip = net.usable[2]
        router = net[2]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth0" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest24.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "vpls"\s*\);' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = \"%s\";' %
                         router, command)
        self.searchoutput(out,
                          r'"system/network/routers" = nlist\(\s*'
                          r'"eth0", list\(\s*"%s"\s*\)\s*\);' % router,
                          command)

    def testmakeunittest25(self):
        command = ["make", "--hostname", "unittest25.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "3/3 compiled", command)

    def testverifyunittest25(self):
        # Verify that the host chooses the closest router
        command = ["cat", "--hostname", "unittest25.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        net = self.net["unknown1"]
        ip = net[4]
        router = net[2]
        self.searchoutput(out,
                          r'"system/network/interfaces/eth1" = nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest25-e1.utcolo.aqd-unittest.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"network_environment", "utcolo",\s*'
                          r'"network_type", "unknown"\s*\);' %
                          (net.broadcast, router, ip, net.netmask),
                          command)
        self.matchoutput(out, '"system/network/default_gateway" = "%s";' %
                         self.net["unknown0"].gateway, command)

    def testmakeaurora(self):
        command = ["make", "--hostname", self.aurora_with_node + ".ms.com"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMake)
    unittest.TextTestRunner(verbosity=2).run(suite)
