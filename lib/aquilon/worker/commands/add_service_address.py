# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ServiceAddress, Host
from aquilon.utils import validate_nlist_key, first_of
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.interface import get_interfaces
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)
from aquilon.worker.processes import DSDBRunner


def add_srv_dsdb_callback(dbsrv, dsdb_runner=None, newly_created=None,
                          comments=None):
    if not newly_created:
        dsdb_runner.delete_host_details(dbsrv.dns_record, dbsrv.ip)

    dsdb_runner.add_host_details(dbsrv.dns_record, dbsrv.ip, comments=comments)
    dsdb_runner.commit_or_rollback("Could not add host to DSDB")


class CommandAddServiceAddress(BrokerCommand):

    required_parameters = ["service_address", "name"]

    def render(self, session, logger, service_address, ip, name, interfaces,
               hostname, cluster, metacluster, resourcegroup,
               network_environment, map_to_primary, comments, **arguments):

        validate_nlist_key("name", name)

        # TODO: generalize the error message - Layer-3 failover may be
        # implemented by other software, not just Zebra.
        if name == "hostname":
            raise ArgumentError("The hostname service address is reserved for "
                                "Zebra.  Please specify the --zebra_interfaces "
                                "option when calling add_host if you want the "
                                "primary name of the host to be managed by "
                                "Zebra.")

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)
        toplevel_holder = holder.toplevel_holder_object

        ServiceAddress.get_unique(session, name=name, holder=holder,
                                  preclude=True)

        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, service_address, ip,
                                                network_environment)
        ip = dbdns_rec.ip

        if map_to_primary:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --map_to_primary option works only "
                                    "for host-based service addresses.")
            dbdns_rec.reverse_ptr = toplevel_holder.hardware_entity.primary_name.fqdn

        dbifaces = []
        if interfaces:
            if isinstance(toplevel_holder, Host):
                dbifaces = get_interfaces(toplevel_holder.hardware_entity,
                                          interfaces, dbdns_rec.network)
            else:
                logger.client_info("The --interfaces option is only valid for "
                                   "host-bound service addresses, and is "
                                   "ignored otherwise.")

        # Disable autoflush, since the ServiceAddress object won't be complete
        # until add_resource() is called
        dsdb_runner = DSDBRunner(logger=logger)
        with session.no_autoflush:
            dbsrv = ServiceAddress(name=name, dns_record=dbdns_rec,
                                   comments=comments)
            holder.resources.append(dbsrv)
            if dbifaces:
                dbsrv.interfaces = dbifaces

        add_resource(session, logger, holder, dbsrv,
                     dsdb_callback=add_srv_dsdb_callback,
                     dsdb_runner=dsdb_runner,
                     newly_created=newly_created, comments=comments)

        return
