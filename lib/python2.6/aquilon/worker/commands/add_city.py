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
"""Contains the logic for `aq add city`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.locks import lock_queue
from aquilon.worker.templates.city import PlenaryCity
from aquilon.worker.commands.add_location import CommandAddLocation


class CommandAddCity(CommandAddLocation):

    required_parameters = ["city", "timezone"]

    def render(self, session, logger, city, country, fullname, comments,
               timezone, campus,
               **arguments):

        if country:
            parentname = country
            parenttype = 'country'
        else:
            parentname = campus
            parenttype = 'campus'

        return CommandAddLocation.render(self, session, city, fullname, 'city',
                                         parentname, parenttype, comments,
                                         logger=logger, timezone=timezone,
                                         campus=campus, **arguments)

    def before_flush(self, session, new_loc, **arguments):

        if "timezone" in arguments:
            new_loc.timezone = arguments["timezone"]

    def after_flush(self, session, new_loc, **arguments):
        logger = arguments["logger"]

        city, country, fullname = (new_loc.name, new_loc.country.name,
                                   new_loc.fullname)

        plenary = PlenaryCity(new_loc, logger=logger)
        key = plenary.get_write_key()
        try:
            lock_queue.acquire(key)
            plenary.write(locked=True)

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.add_city(city, country, fullname)
            dsdb_runner.commit_or_rollback()

        except:
            plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)
