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
"""Contains the logic for `aq update service`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Service
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, logger, service, max_clients, default,
               **arguments):
        dbservice = Service.get_unique(session, name=service, compel=True)
        if default:
            dbservice.max_clients = None
        elif max_clients is not None:
            dbservice.max_clients = max_clients
        else:
            raise ArgumentError("Missing --max_clients or --default argument "
                                "to update service %s." % dbservice.name)
        session.add(dbservice)
        session.flush()

        plenaries = PlenaryCollection()
        plenaries.append(Plenary.get_plenary(dbservice))
        for dbinstance in dbservice.instances:
            plenaries.append(Plenary.get_plenary(dbinstance))
        plenaries.write()

        return
