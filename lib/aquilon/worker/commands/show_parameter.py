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

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Personality
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import get_parameters


class CommandShowParameterPersonality(BrokerCommand):

    required_parameters = ['personality']

    def render(self, session, personality, archetype, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

        parameters = get_parameters(dbpersonality)

        if parameters:
            return parameters

        raise NotFoundException("No parameters found for personality %s." %
                                personality)
