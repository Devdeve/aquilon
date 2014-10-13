#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
"""Module for testing the add feature command."""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddFeature(TestBrokerCommand):

    def test_100_add_host_pre(self):
        command = ["add", "feature", "--feature", "pre_host", "--eon_id", 2,
                   "--type", "host", "--comment", "Test comment"]
        self.noouttest(command)

    def test_100_add_host_post(self):
        command = ["add", "feature", "--feature", "post_host", "--eon_id", 2,
                   "--type", "host", "--post_personality"]
        self.noouttest(command)

    def test_100_add_hw(self):
        command = ["add", "feature", "--feature", "bios_setup",
                   "--eon_id", 2, "--type", "hardware"]
        self.noouttest(command)

    def test_100_add_hw2(self):
        command = ["add", "feature", "--feature", "disable_ht",
                   "--eon_id", 2, "--type", "hardware",
                   "--visibility", "owner_approved"]
        self.noouttest(command)

    def test_100_add_iface(self):
        command = ["add", "feature", "--feature", "src_route",
                   "--eon_id", 2, "--type", "interface",
                   "--visibility", "owner_only"]
        self.noouttest(command)

    def test_110_verify_pre(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: pre_host", command)
        self.matchoutput(out, "Template: features/pre_host", command)
        self.matchoutput(out, "Comments: Test comment", command)
        self.matchoutput(out, "Post Personality: False", command)
        self.matchoutput(out, "Visibility: public", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchclean(out, "Bound to", command)

        command = ["show", "feature", "--feature", "pre_host", "--type", "host", "--format", "proto"]
        out = self.commandtest(command)
        f1 = self.parse_feature_msg(out)
        feature = f1.features[0]
        self.failUnlessEqual(feature.name, "pre_host")
        self.failUnlessEqual(feature.type, "host")
        self.failUnlessEqual(feature.post_personality, False)
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.PUBLIC)

    def test_110_verify_post(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: post_host", command)
        self.matchoutput(out, "Template: features/post_host", command)
        self.matchoutput(out, "Post Personality: True", command)
        self.matchoutput(out, "Visibility: public", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Bound to", command)

        command = ["show", "feature", "--feature", "post_host", "--type", "host", "--format", "proto"]
        out = self.commandtest(command)
        f1 = self.parse_feature_msg(out)
        feature = f1.features[0]
        self.failUnlessEqual(feature.name, "post_host")
        self.failUnlessEqual(feature.type, "host")
        self.failUnlessEqual(feature.post_personality, True)
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.PUBLIC)

    def test_110_verify_hw(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hardware Feature: bios_setup", command)
        self.matchoutput(out, "Template: features/hardware/bios_setup", command)
        self.matchclean(out, "Post Personality", command)
        self.matchoutput(out, "Visibility: public", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Bound to", command)

        command = ["show", "feature", "--feature", "bios_setup", "--type", "hardware", "--format", "proto"]
        out = self.commandtest(command)
        f1 = self.parse_feature_msg(out)
        feature = f1.features[0]
        self.failUnlessEqual(feature.name, "bios_setup")
        self.failUnlessEqual(feature.type, "hardware")
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.PUBLIC)

    def test_110_verify_iface(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.matchoutput(out, "Interface Feature: src_route", command)
        self.matchoutput(out, "Template: features/interface/src_route", command)
        self.matchclean(out, "Post Personality", command)
        self.matchoutput(out, "Visibility: owner_only", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Bound to", command)

        command = ["show", "feature", "--feature", "src_route", "--type", "interface", "--format", "proto"]
        out = self.commandtest(command)
        f1 = self.parse_feature_msg(out)
        feature = f1.features[0]
        self.failUnlessEqual(feature.name, "src_route")
        self.failUnlessEqual(feature.type, "interface")
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.OWNER_ONLY)

    def test_120_show_all(self):
        command = ["show", "feature", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: pre_host", command)
        self.matchoutput(out, "Host Feature: post_host", command)
        self.matchoutput(out, "Hardware Feature: bios_setup", command)
        self.matchoutput(out, "Interface Feature: src_route", command)

        command = ["show", "feature", "--all", "--format", "proto"]
        out = self.commandtest(command)
        f1 = self.parse_feature_msg(out)
        feature = f1.features[0]
        self.failUnlessEqual(feature.name, "bios_setup")
        self.failUnlessEqual(feature.type, "hardware")
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.PUBLIC)
        feature = f1.features[1]
        self.failUnlessEqual(feature.name, "disable_ht")
        self.failUnlessEqual(feature.visibility, feature.OWNER_APPROVED)
        feature = f1.features[2]
        self.failUnlessEqual(feature.name, "pre_host")
        self.failUnlessEqual(feature.type, "host")
        self.failUnlessEqual(feature.post_personality, False)
        self.failUnlessEqual(feature.owner_eonid, 2)
        feature = f1.features[3]
        self.failUnlessEqual(feature.name, "post_host")
        self.failUnlessEqual(feature.type, "host")
        self.failUnlessEqual(feature.post_personality, True)
        self.failUnlessEqual(feature.owner_eonid, 2)
        feature = f1.features[4]
        self.failUnlessEqual(feature.name, "src_route")
        self.failUnlessEqual(feature.type, "interface")
        self.failUnlessEqual(feature.owner_eonid, 2)
        self.failUnlessEqual(feature.visibility, feature.OWNER_ONLY)


    def test_200_post_hw(self):
        command = ["add", "feature", "--feature", "post_hw",
                   "--eon_id", 2, "--type", "hardware", "--post_personality"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "The post_personality attribute is implemented "
                         "only for host features.", command)

    def test_200_post_iface(self):
        command = ["add", "feature", "--feature", "post_iface",
                   "--eon_id", 2, "--type", "interface", "--post_personality"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "The post_personality attribute is implemented "
                         "only for host features.", command)

    def test_200_hw_prefix(self):
        command = ["add", "feature", "--feature", "hardware/host",
                   "--eon_id", 2, "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The 'hardware/' and 'interface/' prefixes "
                         "are not available for host features.", command)

    def test_200_iface_prefix(self):
        command = ["add", "feature", "--feature", "interface/host",
                   "--eon_id", 2, "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The 'hardware/' and 'interface/' prefixes "
                         "are not available for host features.", command)

    def test_200_dotdot_begin(self):
        # Use os.path.join() to test the natural path separator of the platform
        path = os.path.join("..", "foo")
        command = ["add", "feature", "--feature", path, "--type", "host", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Path components in the feature name must not "
                         "start with a dot.", command)

    def test_200_dotdot_middle(self):
        # Use os.path.join() to test the natural path separator of the platform
        path = os.path.join("foo", "..", "bar")
        command = ["add", "feature", "--feature", path, "--type", "host", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Path components in the feature name must not "
                         "start with a dot.", command)

    def test_200_hidden_begin(self):
        command = ["add", "feature", "--feature", ".foo", "--type", "host", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Path components in the feature name must not "
                         "start with a dot.", command)

    def test_200_hidden_middle(self):
        command = ["add", "feature", "--feature", "foo/.bar", "--type", "host", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Path components in the feature name must not "
                         "start with a dot.", command)

    def test_210_verify_post_hw(self):
        command = ["show", "feature", "--feature", "post_hw",
                   "--type", "hardware"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature post_hw not found.",
                         command)

    def test_210_verify_post_iface(self):
        command = ["show", "feature", "--feature", "post_iface",
                   "--type", "interface"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature post_iface not found.",
                         command)

    def test_210_verify_hw_prefix(self):
        command = ["show", "feature", "--feature", "hardware/host",
                   "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature hardware/host not found.",
                         command)

    def test_210_verify_iface_prefix(self):
        command = ["show", "feature", "--feature", "interface/host",
                   "--type", "interface"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature interface/host not found.",
                         command)

    def test_220_type_mismatch(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature bios_setup not found.",
                         command)

    def test_230_add_again(self):
        command = ["add", "feature", "--feature", "pre_host", "--type", "host", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host Feature pre_host already exists.", command)

    def test_240_add_bad_type(self):
        command = ["add", "feature", "--feature", "bad-type",
                   "--type", "no-such-type", "--eon_id", 2]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown feature type 'no-such-type'. The "
                         "valid values are: hardware, host, interface.",
                         command)

    def test_240_show_bad_type(self):
        command = ["show", "feature", "--feature", "bad-type",
                   "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown feature type 'no-such-type'. The "
                         "valid values are: hardware, host, interface.",
                         command)

    def test_300_update_feature(self):
        command = ["update", "feature", "--feature", "pre_host", "--eon_id", 3,
                   "--type", "host", "--comment", "New comment", "--visibility", "restricted"]
        self.noouttest(command)

        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: pre_host", command)
        self.matchoutput(out, "Template: features/pre_host", command)
        self.matchoutput(out, "Comments: New comment", command)
        self.matchoutput(out, "Post Personality: False", command)
        self.matchoutput(out, "Visibility: restricted", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
