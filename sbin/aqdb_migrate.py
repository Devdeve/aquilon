#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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

# Copy AQDB to a different backend.
#
# The source backend is taken from $AQDCONF as usual, the destination backend
# is taken from command line.
#
# Warning: making a copy will cause the sequences in the source database to
# jump - there's no easy way around that.
#
# Examples:
#    ./aqdb_migrate sqlite:////path/aquilon.db
#    ./aqdb_migrate postgresql://<username>@/

from __future__ import print_function

import os
import signal
import sys

# -- begin path_setup --
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
LIBDIR = os.path.join(BINDIR, "..", "lib")

if LIBDIR not in sys.path:
    sys.path.append(LIBDIR)
# -- end path_setup --

from aquilon.aqdb import depends  # pylint: disable=W0611

import argparse

from sqlalchemy import create_engine, Table
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Base

signalled = 0


def dummy_mapper(table):
    Base = declarative_base()

    class DummyMapper(Base):
        __table__ = table

    return DummyMapper


def signal_handler(signum, frame):
    global signalled
    signalled = 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='copy AQDB between backends')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        help='show queries (metadata bind.echo = True)')
    parser.add_argument('dsn', metavar='DSN',
                        help='DSN of the target backend (driver://user[:password]@host[:port]/database)')
    opts = parser.parse_args()

    # Use aquilon.aqdb for connecting to the source backend
    db = DbFactory()
    if opts.verbose:
        db.engine.echo = True
    src_session = sessionmaker(bind=db.engine)()

    if db.engine.dialect.name == 'oracle' or \
       db.engine.dialect.name == 'postgresql':
        src_session.execute(text('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'))

    dest_engine = create_engine(opts.dsn, convert_unicode=True, echo=opts.verbose)
    dest_session = sessionmaker(bind=dest_engine)()

    if db.engine.dialect.supports_sequences and \
       dest_engine.dialect.supports_sequences:
        # The only operation on sequences that all DBs support is getting the
        # next value. Unfortunately that means we have to alter the state of the
        # source database here.
        for seq in Base.metadata._sequences.values():
            nextid = src_session.execute(seq)
            # Make sure the sequence is re-created with the right start index
            seq.drop(dest_engine, checkfirst=True)
            seq.start = nextid

    # Avoid auto-populating tables as that would interfere with the copying
    Base.populate_table_on_create = False

    # Need to call this explicitely to make the __extra_table_args__ hack work
    configure_mappers()

    Base.metadata.create_all(dest_engine, checkfirst=True)

    if dest_engine.dialect.name == 'postgresql':
        dest_session.execute(text('SET CONSTRAINTS ALL DEFERRED'))
    elif dest_engine.dialect.name == 'oracle':
        dest_session.execute(text('ALTER SESSION SET CONSTRAINTS = DEFERRED'))
    elif dest_engine.dialect.name == 'sqlite':
        # SQLite does not allow changing the deferred state at run-time, but
        # it does allow disabling foreign keys entirely
        dest_session.execute(text('PRAGMA foreign_keys = 0;'))

    signal.signal(signal.SIGALRM, signal_handler)

    # Oracle does not like EINTR
    signal.siginterrupt(signal.SIGALRM, False)

    for table in Base.metadata.sorted_tables:
        total = src_session.execute(table.count()).scalar()
        print('Processing %s (%d rows)' % (table, total), end=' ')
        sys.stdout.flush()
        cnt = 0

        NewRecord = dummy_mapper(table)
        signal.setitimer(signal.ITIMER_REAL, 5, 5)
        for record in src_session.execute(table.select()):
            cnt = cnt + 1
            if signalled:
                print("... %d" % cnt, end=' ')
                sys.stdout.flush()
                signalled = 0

            data = dict(
                [(str(colname), getattr(record, colname))
                 for colname in table.columns]
            )

            # insert() is faster, but using .merge() is restartable
            # dest_session.merge(NewRecord(**data))
            dest_session.execute(table.insert().values(**data))

        signal.setitimer(signal.ITIMER_REAL, 0)
        dest_session.flush()
        print()

    dest_session.commit()
