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
"""Model formatter."""

from aquilon.aqdb.model import Model
from aquilon.worker.formats.formatters import ObjectFormatter


class ModelFormatter(ObjectFormatter):
    def format_raw(self, model, indent=""):
        details = [indent + "Vendor: %s Model: %s" %
                   (model.vendor.name, model.name)]
        details.append(indent + "  Type: %s" % str(model.model_type))
        for link in model.features:
            details.append(indent + "  {0:c}: {0.name}".format(link.feature))
            if link.archetype:
                details.append(indent + "    {0:c}: {0.name}"
                               .format(link.archetype))
            if link.personality:
                details.append(indent + "    {0:c}: {0.name} {1:c}: {1.name}"
                               .format(link.personality,
                                       link.personality.archetype))
            if link.interface_name:
                details.append(indent + "    Interface: %s" %
                               link.interface_name)
        if model.comments:
            details.append(indent + "  Comments: %s" % model.comments)
        if model.machine_specs:
            details.append(self.redirect_raw(model.machine_specs, indent + "  "))
        return "\n".join(details)

    def fill_proto(self, model, skeleton):
        skeleton.name = str(model.name)
        skeleton.vendor = str(model.vendor.name)
        skeleton.model_type = str(model.model_type)

ObjectFormatter.handlers[Model] = ModelFormatter()
