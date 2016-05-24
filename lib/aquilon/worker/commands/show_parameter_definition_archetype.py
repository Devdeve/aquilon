# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016  Contributor
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

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Archetype, ParamDefinition
from aquilon.worker.broker import BrokerCommand


class CommandShowParameterDefinitionArchetype(BrokerCommand):

    required_parameters = ["archetype", "path"]

    def render(self, session, archetype, path, **_):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        for holder in dbarchetype.param_def_holders.values():
            db_paramdef = ParamDefinition.get_unique(session, path=path,
                                                     holder=holder)
            if db_paramdef:
                break
        else:
            raise NotFoundException("Parameter definition %s not found." % path)

        return db_paramdef
