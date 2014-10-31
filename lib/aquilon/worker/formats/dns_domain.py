# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""DNS Domain formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import DnsDomain


class DnsDomainFormatter(ObjectFormatter):
    def format_raw(self, dns_domain, indent=""):
        details = [indent + "DNS Domain: %s" % dns_domain.name]
        details.append(indent + "  Restricted: %s" % dns_domain.restricted)

        if len(dns_domain.servers) > 0:
            server_list = ','.join(str(srv) for srv in dns_domain.servers)
            details.append(indent + "  Servers: %s" % server_list)

        for location in dns_domain.mapped_locations:
            details.append(indent + "  Mapped to: {0}".format(location))
        if dns_domain.comments:
            details.append(indent + "  Comments: %s" % dns_domain.comments)

        return "\n".join(details)

    def csv_fields(self, dns_domain):
        yield (dns_domain.name, dns_domain.comments)

    def format_proto(self, dns_domain, container):
        skeleton = container.dns_domains.add()
        self.add_dns_domain_data(skeleton, dns_domain)

ObjectFormatter.handlers[DnsDomain] = DnsDomainFormatter()
