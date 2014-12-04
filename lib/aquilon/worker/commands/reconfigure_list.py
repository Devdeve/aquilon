# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq reconfigure --list`."""

from collections import defaultdict

from sqlalchemy.orm import joinedload, subqueryload, undefer

from aquilon.exceptions_ import (ArgumentError, NotFoundException,
                                 IncompleteError)
from aquilon.aqdb.model import (Archetype, Personality, OperatingSystem,
                                HostLifecycle)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            preload_machine_data,
                                            check_hostlist_size,
                                            validate_branch_author)
from aquilon.worker.templates import PlenaryCollection, TemplateDomain
from aquilon.worker.services import Chooser


class CommandReconfigureList(BrokerCommand):

    required_parameters = ["list"]

    def get_hostlist(self, session, list, **arguments):   # pylint: disable=W0613
        check_hostlist_size(self.command, self.config, list)
        options = [joinedload('personality'),
                   subqueryload('personality.grns'),
                   subqueryload('grns'),
                   subqueryload('services_used'),
                   undefer('services_used._client_count'),
                   subqueryload('services_provided'),
                   joinedload('resholder'),
                   subqueryload('resholder.resources'),
                   joinedload('_cluster'),
                   subqueryload('_cluster.cluster'),
                   joinedload('hardware_entity.model'),
                   subqueryload('hardware_entity.interfaces'),
                   subqueryload('hardware_entity.interfaces.assignments'),
                   subqueryload('hardware_entity.interfaces.assignments.dns_records'),
                   joinedload('hardware_entity.interfaces.assignments.network'),
                   joinedload('hardware_entity.location'),
                   subqueryload('hardware_entity.location.parents')]
        dbhosts = hostlist_to_hosts(session, list, options)
        preload_machine_data(session, dbhosts)
        return dbhosts

    def render(self, session, logger, archetype, personality, keepbindings,
               buildstatus, osname, osversion, grn, eon_id, cleargrn,
               **arguments):
        dbhosts = self.get_hostlist(session, **arguments)

        if archetype:
            target_archetype = Archetype.get_unique(session, archetype, compel=True)
            if target_archetype.cluster_type is not None:
                raise ArgumentError("{0} is a cluster archetype, it cannot be "
                                    "used for hosts.".format(target_archetype))
        else:
            target_archetype = None

        if buildstatus:
            dbstatus = HostLifecycle.get_instance(session, buildstatus)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)

        # Take a shortcut if there's nothing to do
        if not dbhosts:
            return

        dbbranch, dbauthor = validate_branch_author(dbhosts)

        failed = []
        personality_cache = defaultdict(dict)
        os_cache = defaultdict(dict)

        for dbhost in dbhosts:
            old_archetype = dbhost.archetype
            if target_archetype:
                dbarchetype = target_archetype
            else:
                dbarchetype = dbhost.archetype

            if personality or old_archetype != dbarchetype:
                if not personality:
                    personality = dbhost.personality.name

                # Cache personalities to avoid looking up the same data many
                # times
                if personality in personality_cache[dbarchetype]:
                    dbpersonality = personality_cache[dbarchetype][personality]
                else:
                    try:
                        dbpersonality = Personality.get_unique(session, name=personality,
                                                               archetype=dbarchetype,
                                                               compel=True)
                        personality_cache[dbarchetype][personality] = dbpersonality
                    except NotFoundException as err:
                        failed.append("%s: %s" % (dbhost.fqdn, err))
                        continue

                if dbhost.cluster and dbhost.cluster.allowed_personalities and \
                   dbpersonality not in dbhost.cluster.allowed_personalities:
                    allowed = sorted(p.qualified_name for p in
                                     dbhost.cluster.allowed_personalities)
                    failed.append("{0}: {1} is not allowed by {2}.  "
                                  "Specify one of: {3}."
                                  .format(dbhost.fqdn, dbpersonality,
                                          dbhost.cluster, ", ".join(allowed)))
                    continue

                dbhost.personality = dbpersonality

            if osname or osversion or old_archetype != dbarchetype:
                if not osname:
                    osname = dbhost.operating_system.name
                if not osversion:
                    osversion = dbhost.operating_system.version

                oskey = "%s/%s" % (osname, osversion)
                if oskey in os_cache[dbarchetype]:
                    dbos = os_cache[dbarchetype][oskey]
                else:
                    try:
                        dbos = OperatingSystem.get_unique(session, name=osname,
                                                          version=osversion,
                                                          archetype=dbarchetype,
                                                          compel=True)
                        os_cache[dbarchetype][oskey] = dbos
                    except NotFoundException as err:
                        failed.append("%s: %s" % (dbhost.fqdn, err))
                        continue

                dbhost.operating_system = dbos

            if grn or eon_id:
                dbhost.owner_grn = dbgrn
            if cleargrn:
                dbhost.owner_grn = None

            if buildstatus:
                dbhost.status.transition(dbhost, dbstatus)

        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))

        session.flush()

        logger.client_info("Verifying service bindings.")
        choosers = []
        for dbhost in dbhosts:
            if dbhost.archetype.is_compileable:
                chooser = Chooser(dbhost, logger=logger,
                                  required_only=not keepbindings)
                choosers.append(chooser)
                try:
                    chooser.set_required()
                except ArgumentError as e:
                    failed.append(str(e))
        if failed:
            raise ArgumentError("The following hosts failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        for chooser in choosers:
            plenaries.append(chooser.plenaries)
        plenaries.flatten()

        td = TemplateDomain(dbbranch, dbauthor, logger=logger)

        # Don't bother locking until every possible check before the
        # actual writing and compile is done.  This will allow for fast
        # turnaround on errors (no need to wait for a lock if there's
        # a missing service map entry or something).
        with plenaries.get_key():
            plenaries.stash()
            try:
                errors = []
                for template in plenaries.plenaries:
                    try:
                        template.write(locked=True)
                    except IncompleteError as err:
                        # Ignore IncompleteError for hosts added indirectly,
                        # e.g. servers of service instances. It is debatable
                        # if this is the right thing to do, but it preserves the
                        # status quo, and can be revisited later.
                        if template.dbobj not in dbhosts:
                            logger.client_info("Warning: %s" % err)
                        else:
                            errors.append(str(err))

                if errors:
                    raise ArgumentError("\n".join(errors))
                td.compile(session, only=plenaries.object_templates,
                           locked=True)
            except:
                plenaries.restore_stash()
                raise

        return
