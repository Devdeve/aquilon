# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Contains the logic for `aq reset advertised status --list`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            check_hostlist_size)
from aquilon.worker.commands.reset_advertised_status \
     import CommandResetAdvertisedStatus
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey


class CommandResetAdvertisedStatusList(CommandResetAdvertisedStatus):
    """ reset advertised status for a list of hosts """

    required_parameters = ["list"]

    def render(self, session, logger, list, **arguments):
        check_hostlist_size(self.command, self.config, list)
        dbhosts = hostlist_to_hosts(session, list)

        self.resetadvertisedstatus_list(session, logger, dbhosts)

    def resetadvertisedstatus_list(self, session, logger, dbhosts):
        branches = {}
        authors = {}
        failed = []
        compileable = []
        # Do any cross-list or dependency checks
        for dbhost in dbhosts:
            ## if archetype is compileable only then
            ## validate for branches and domains
            if (dbhost.archetype.is_compileable):
                compileable.append(dbhost.fqdn)
                if dbhost.branch in branches:
                    branches[dbhost.branch].append(dbhost)
                else:
                    branches[dbhost.branch] = [dbhost]
                if dbhost.sandbox_author in authors:
                    authors[dbhost.sandbox_author].append(dbhost)
                else:
                    authors[dbhost.sandbox_author] = [dbhost]

            if dbhost.status.name == 'ready':
                failed.append("{0:l} is in ready status, "
                              "advertised status can be reset only "
                              "when host is in non ready state".format(dbhost))
        if failed:
            raise ArgumentError("Cannot modify the following hosts:\n%s" %
                                "\n".join(failed))
        if len(branches) > 1:
            keys = branches.keys()
            branch_sort = lambda x, y: cmp(len(branches[x]), len(branches[y]))
            keys.sort(cmp=branch_sort)
            stats = ["{0:d} hosts in {1:l}".format(len(branches[branch]),
                                                   branch)
                     for branch in keys]
            raise ArgumentError("All hosts must be in the same domain or "
                                "sandbox:\n%s" % "\n".join(stats))
        if len(authors) > 1:
            keys = authors.keys()
            author_sort = lambda x, y: cmp(len(authors[x]), len(authors[y]))
            keys.sort(cmp=author_sort)
            stats = ["%s hosts with sandbox author %s" %
                     (len(authors[author]), author.name) for author in keys]
            raise ArgumentError("All hosts must be managed by the same "
                                "sandbox author:\n%s" % "\n".join(stats))

        plenaries = PlenaryCollection(logger=logger)
        for dbhost in dbhosts:
            dbhost.advertise_status = False
            session.add(dbhost)
            plenaries.append(PlenaryHost(dbhost, logger=logger))

        session.flush()

        dbbranch = branches.keys()[0]
        dbauthor = authors.keys()[0]
        key = CompileKey.merge([plenaries.get_write_key()])
        try:
            lock_queue.acquire(key)
            plenaries.stash()
            plenaries.write(locked=True)
            td = TemplateDomain(dbbranch, dbauthor, logger=logger)
            td.compile(session, only=compileable, locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
