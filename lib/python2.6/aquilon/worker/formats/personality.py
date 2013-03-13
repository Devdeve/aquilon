# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
""" Personality formatter """

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Personality


class ThresholdedPersonality(object):
    def __init__(self, dbpersonality, thresholds):
        self.dbpersonality = dbpersonality
        if not thresholds:
            thresholds = {}
        self.threshold = thresholds.get('threshold')
        self.maintenance_threshold = thresholds.get('maintenance_threshold')


class PersonalityList(list):
    """Holds instances of ThresholdedPersonality."""


class PersonalityListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, tpl, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].PersonalityList()
        for personality in tpl:
            self.redirect_proto(personality, skeleton.personalities.add())
        return skeleton


class PersonalityFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, personality, indent=""):
        # Transparently handle Personality and ThresholdedPersonality
        has_threshold = False
        if hasattr(personality, "dbpersonality"):
            threshold = personality.threshold
            maintenance_threshold = personality.maintenance_threshold
            has_threshold = True
            personality = personality.dbpersonality
        description = "Host"
        if personality.is_cluster:
            description = "Cluster"
        details = [indent + "%s Personality: %s" % (description,
                                                    personality) +
                   " Archetype: %s" % personality.archetype]
        details.append(indent +
                       "  Environment: %s" % personality.host_environment)
        details.append(indent + "  Owned by {0:c}: {0.grn}"
                       .format(personality.owner_grn))
        for grn in personality.grns:
            details.append(indent + "  Used by {0:c}: {0.grn}".format(grn))

        if personality.config_override:
            details.append(indent + "  Config override: enabled")

        details.append(indent + "  Template: %s/personality/%s/config.tpl" %
                       (personality.archetype, personality))

        if has_threshold:
            details.append(indent + "  Threshold: %s" % threshold)
            details.append(indent + "  Maintenance Threshold: %s" %
                           maintenance_threshold)
        if personality.cluster_required:
            details.append(indent + "  Requires clustered hosts")
        for service in personality.services:
            details.append(indent + "  Required Service: %s" % service.name)

        features = personality.features[:]
        features.sort(key=lambda x: (x.feature.feature_type,
                                     x.feature.post_personality,
                                     x.feature.name))

        for link in features:
            if link.feature.post_personality:
                flagstr = " [post_personality]"
            elif link.feature.post_personality_allowed:
                flagstr = " [pre_personality]"
            else:
                flagstr = ""

            details.append(indent + "  {0:c}: {0.name}{1}"
                           .format(link.feature, flagstr))
            if link.model:
                details.append(indent + "    {0:c}: {0.name} {1:c}: {1.name}"
                               .format(link.model.vendor, link.model))
            if link.interface_name:
                details.append(indent + "    Interface: %s" %
                               link.interface_name)

        if personality.comments:
            details.append(indent + "  Comments: %s" % personality.comments)

        for cltype, info in personality.cluster_infos.items():
            details.append(indent + "  Extra settings for %s clusters:" % cltype)
            if cltype == "esx":
                details.append(indent + "    VM host capacity function: %s" %
                               info.vmhost_capacity_function)
                details.append(indent + "    VM host overcommit factor: %s" %
                               info.vmhost_overcommit_memory)
        return "\n".join(details)

    def format_proto(self, personality, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].PersonalityList()
            skeleton = container.personalities.add()
        # Transparently handle Personality and ThresholdedPersonality
        threshold = None
        if hasattr(personality, "dbpersonality"):
            threshold = personality.threshold
            personality = personality.dbpersonality

        self.add_personality_data(skeleton, personality)
        if threshold is not None:
            skeleton.threshold = threshold

        if personality.grns:
            skeleton.owner_eonid = personality.grns[0].eon_id

        features = personality.features[:]
        features.sort(key=lambda x: (x.feature.feature_type,
                                     x.feature.post_personality,
                                     x.feature.name))

        for link in features:
            self.add_featurelink_msg(skeleton.features.add(), link)

        for service in personality.services:
            rsvc_msg = skeleton.required_services.add()
            rsvc_msg.service = service.name

        if personality.comments:
            skeleton.comments = personality.comments

        skeleton.config_override = personality.config_override
        skeleton.cluster_required = personality.cluster_required

        return container


ObjectFormatter.handlers[Personality] = PersonalityFormatter()
ObjectFormatter.handlers[ThresholdedPersonality] = PersonalityFormatter()
ObjectFormatter.handlers[PersonalityList] = PersonalityListFormatter()
