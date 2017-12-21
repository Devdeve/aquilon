# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2016,2017  Contributor
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

from aquilon.aqdb.model import (OperatingSystem, Archetype,
                                AssetLifecycle)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateOS(BrokerCommand):

    required_parameters = ["osname", "osversion", "archetype"]

    def render(self, session, osname, osversion, archetype, lifecycle, comments,
               user, justification, reason, logger, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)

        if comments is not None:
            dbos.comments = comments

        if lifecycle:
            # Validate ChangeManagement
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
            cm.consider(dbos)
            cm.validate()

            dblifecycle = AssetLifecycle.get_instance(session, lifecycle)
            dbos.lifecycle.transition(dbos, dblifecycle)

        session.flush()

        return
