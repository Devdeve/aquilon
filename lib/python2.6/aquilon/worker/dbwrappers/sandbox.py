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
"""Wrapper to make getting a sandbox simpler."""


from aquilon.aqdb.model import Sandbox
from aquilon.worker.dbwrappers.user_principal import get_user_principal


def get_sandbox(session, logger, sandbox):
    """Allow an optional author field."""
    sbx_split = sandbox.split('/')
    first, second = '', ''
    if len(sbx_split) <= 1:
        dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)
        dbauthor = None
        return (dbsandbox, dbauthor)
    first = '/'.join(sbx_split[:-1])
    second = sbx_split[-1]
    dbsandbox = Sandbox.get_unique(session, second, compel=True)
    dbauthor = get_user_principal(session, first)
    return (dbsandbox, dbauthor)
