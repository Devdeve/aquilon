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
""" Observed Mac's are represent the occurance of seeing a mac address on
    the cam table of a given switch. They are created to allow for automated
    machine builds and ip assignment """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Switch
from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.column_types import AqStr

_TN = 'observed_mac'


class ObservedMac(Base):
    """ reports the observance of a mac address on a switch port. """
    __tablename__ = _TN

    switch_id = Column(Integer, ForeignKey('switch.hardware_entity_id',
                                           ondelete='CASCADE',
                                           name='obs_mac_hw_fk'),
                       nullable=False)

    port = Column(AqStr(32), nullable=False)

    mac_address = Column(AqMac(17), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    last_seen = Column('last_seen', DateTime,
                       default=datetime.now, nullable=False)

    switch = relation(Switch, backref=backref('observed_macs',
                                              cascade='delete',
                                              order_by=[port]))

    __table_args__ = (PrimaryKeyConstraint(switch_id, port, mac_address),)
