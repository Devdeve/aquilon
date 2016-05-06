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
"""Contains the logic for `aq add service`."""

from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandAddService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, logger, service, need_client_list, comments, **_):
        Service.get_unique(session, service, preclude=True)
        dbservice = Service(name=service, comments=comments,
                            need_client_list=need_client_list)
        session.add(dbservice)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbservice))

        session.flush()
        plenaries.write()
        return
