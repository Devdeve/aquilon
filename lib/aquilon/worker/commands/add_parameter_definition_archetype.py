# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import Archetype, ArchetypeParamDef, ParamDefinition
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import validate_param_definition


class CommandAddParameterDefintionArchetype(BrokerCommand):

    required_parameters = ["archetype", "template", "path", "value_type"]

    def render(self, session, logger, archetype, template, path, value_type,
               required, activation, default, description, **kwargs):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not dbarchetype.is_compileable:
            raise ArgumentError("{0} is not compileable.".format(dbarchetype))

        if not dbarchetype.param_def_holder:
            dbarchetype.param_def_holder = ArchetypeParamDef()

        # strip slash from path start and end
        if path.startswith("/"):
            path = path[1:]
        if path.endswith("/"):
            path = path[:-1]

        if not activation:
            activation = 'dispatch'
        if activation == 'rebuild' and default:
            raise UnimplementedError("Setting a default value for a parameter "
                                     "which requires rebuild would cause all "
                                     "existing hosts to require a rebuild, "
                                     "which is not supported.")

        validate_param_definition(path, value_type, default)

        ParamDefinition.get_unique(session, path=path,
                                   holder=dbarchetype.param_def_holder, preclude=True)

        db_paramdef = ParamDefinition(path=path,
                                      holder=dbarchetype.param_def_holder,
                                      value_type=value_type, default=default,
                                      required=required, template=template,
                                      activation=activation,
                                      description=description)
        session.add(db_paramdef)

        session.flush()

        if default:
            logger.client_info("You need to run 'aq flush --personalities' for "
                               "the default value to take effect.")

        return
