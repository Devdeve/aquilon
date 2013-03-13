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


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.manage_hostname import validate_branch_commits
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue, CompileKey


class CommandManageCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, domain, sandbox, cluster, force,
               **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing clusters to {0:l} is not allowed."
                                .format(dbbranch))

        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbsource = dbcluster.branch
        dbsource_author = dbcluster.sandbox_author
        old_branch = dbcluster.branch.name

        if not force:
            validate_branch_commits(dbsource, dbsource_author,
                                    dbbranch, dbauthor, logger, self.config)

        if dbcluster.metacluster:
            raise ArgumentError("{0.name} is member of metacluster {1.name}, "
                                "it must be managed at metacluster level.".
                                format(dbcluster, dbcluster.metacluster))

        old_branch = dbcluster.branch.name
        plenaries = PlenaryCollection(logger=logger)

        # manage at metacluster level
        if dbcluster.cluster_type == 'meta':
            clusters = dbcluster.members

            dbcluster.branch = dbbranch
            dbcluster.sandbox_author = dbauthor
            session.add(dbcluster)
            plenaries.append(Plenary.get_plenary(dbcluster))
        else:
            clusters = [dbcluster]

        for cluster in clusters:
            # manage at cluster level
            # Need to set the new branch *before* creating the plenary objects.
            cluster.branch = dbbranch
            cluster.sandbox_author = dbauthor
            session.add(cluster)
            plenaries.append(Plenary.get_plenary(cluster))
            for dbhost in cluster.hosts:
                dbhost.branch = dbbranch
                dbhost.sandbox_author = dbauthor
                session.add(dbhost)
                plenaries.append(Plenary.get_plenary(dbhost))

        session.flush()

        # We're crossing domains, need to lock everything.
        key = CompileKey(logger=logger)
        try:
            lock_queue.acquire(key)
            plenaries.stash()
            plenaries.cleanup(old_branch, locked=True)
            plenaries.write(locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
