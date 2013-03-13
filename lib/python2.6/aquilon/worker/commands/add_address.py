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

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_address_dns_environment \
        import CommandAddAddressDNSEnvironment


class CommandAddAddress(CommandAddAddressDNSEnvironment):

    required_parameters = ["fqdn"]

    def render(self, dns_environment, network_environment, **kwargs):

        if not (network_environment or dns_environment):
            dns_environment = self.config.get("site", "default_dns_environment")
        return CommandAddAddressDNSEnvironment.render(self,
                                                      dns_environment=dns_environment,
                                                      network_environment=network_environment,
                                                      **kwargs)
