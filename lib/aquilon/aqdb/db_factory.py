# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""To be imported by classes and modules requiring aqdb access"""

import re
import os
import sys
import logging
import time
from numbers import Number

from aquilon.aqdb import depends  # pylint: disable=W0611
from aquilon.config import Config
from aquilon.utils import monkeypatch
from aquilon.exceptions_ import AquilonError

from sqlalchemy.exc import DatabaseError
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import CreateIndex, Sequence
from sqlalchemy.dialects.oracle.base import OracleDDLCompiler


# Add support for Oracle-specific index extensions
@compiles(CreateIndex, 'oracle')
def visit_create_index(create, compiler, **kw):  # pragma: no cover
                                                 # pylint: disable=W0613
    index = create.element
    compiler._verify_index_table(index)
    preparer = compiler.preparer

    text = "CREATE "  # pylint: disable=W0621
    if index.unique:
        text += "UNIQUE "
    if index.kwargs.get("oracle_bitmap", False):
        text += "BITMAP "

    text += "INDEX %s ON %s (%s)" \
        % (compiler._prepared_index_name(index, include_schema=True),
           preparer.format_table(index.table, use_schema=True),
           ', '.join(compiler.sql_compiler.process(expr, include_table=False,
                                                   literal_binds=True)
                     for expr in index.expressions))

    compress = index.kwargs.get("oracle_compress", False)
    if compress:
        if isinstance(compress, Number):
            text += " COMPRESS %d" % compress
        else:
            text += " COMPRESS"

    return text


# Add support for table compression
@monkeypatch(OracleDDLCompiler)
def post_create_table(self, table):  # pragma: no cover
                                     # pylint: disable=W0613
    text = ""  # pylint: disable=W0621
    compress = table.kwargs.get("oracle_compress", False)
    if compress:
        if isinstance(compress, basestring):
            text += " COMPRESS FOR " + compress.upper()
        else:
            text += " COMPRESS"

    return text


def sqlite_foreign_keys(dbapi_con, con_record):  # pylint: disable=W0613
    dbapi_con.execute('pragma foreign_keys=ON')


def sqlite_no_fsync(dbapi_con, con_record):  # pylint: disable=W0613
    dbapi_con.execute('pragma synchronous=OFF')


def oracle_set_module(dbapi_con, con_record):  # pylint: disable=W0613
    # Store the program's name in v$session. Trying to set a value longer than
    # the allowed length will generate ORA-24960, so do an explicit truncation.
    prog = os.path.basename(sys.argv[0])
    dbapi_con.module = prog[:48]


def oracle_reset_action(dbapi_con, con_record):  # pylint: disable=W0613
    # Reset action and clientinfo in v$session. The DB connection may be closed
    # when this function is called, so be careful.
    if dbapi_con is None:
        return
    try:
        dbapi_con.action = ""
        dbapi_con.clientinfo = ""
    except:
        pass


def timer_start(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    conn.info.setdefault('query_start_time', []).append(time.time())


def timer_stop(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    total = time.time() - conn.info['query_start_time'].pop(-1)
    log = logging.getLogger(__name__)
    log.info("Query running time: %f", total)


class DbFactory(object):
    __shared_state = {}
    __started = False  # at the class definition, that is

    def create_engine(self, config, dsn, **pool_options):
        engine = create_engine(dsn, **pool_options)

        if engine.dialect.name == "oracle":
            event.listen(engine, "connect", oracle_set_module)
            event.listen(engine, "checkin", oracle_reset_action)
        elif engine.dialect.name == "sqlite":
            event.listen(engine, "connect", sqlite_foreign_keys)
            if config.has_option("database", "disable_fsync") and \
               config.getboolean("database", "disable_fsync"):
                event.listen(engine, "connect", sqlite_no_fsync)
                log = logging.getLogger(__name__)
                log.info("SQLite is operating in unsafe mode!")
        elif engine.dialect.name == "postgresql":
            pass

        if self.verbose:
            engine.echo = True

        if config.has_option("database", "log_query_times") and \
           config.getboolean("database", "log_query_times"):
            event.listen(engine, "before_cursor_execute", timer_start)
            event.listen(engine, "after_cursor_execute", timer_stop)

        return engine

    def __init__(self, verbose=False):
        self.__dict__ = self.__shared_state

        if self.__started:
            return

        self.__started = True
        self.verbose = verbose

        config = Config()
        log = logging.getLogger(__name__)

        if config.has_option("database", "module"):
            from ms.modulecmd import Modulecmd, ModulecmdExecError

            module = config.get("database", "module")
            cmd = Modulecmd()
            try:
                log.info("Loading module %s.", module)
                cmd.load(module)
            except ModulecmdExecError as err:
                log.error("Failed to load module %s: %s", module, err)

        pool_options = {}

        for optname in ("pool_size", "pool_timeout", "pool_recycle"):
            if config.has_option("database", optname):
                if len(config.get("database", optname).strip()) > 0:
                    pool_options[optname] = config.getint("database", optname)
                else:
                    # pool_timeout can be set to None
                    pool_options[optname] = None

        # Sigh. max_overflow does not start with pool_*
        if config.has_option("database", "pool_max_overflow"):
            pool_options["max_overflow"] = config.getint("database",
                                                         "pool_max_overflow")
        log.info("Database engine using pool options %s", pool_options)

        dsn = config.get('database', 'dsn')
        dialect = make_url(dsn).get_dialect()

        if dialect.name == "oracle":
            self.login(config, dsn, pool_options)
        elif dialect.name == "postgresql":
            self.login(config, dsn, pool_options)
        elif dialect.name == "sqlite":
            self.engine = self.create_engine(config, dsn)
            self.no_lock_engine = None
            connection = self.engine.connect()
            connection.close()
        else:
            raise AquilonError("Supported database datasources are postgresql, "
                               "oracle and sqlite. You've asked for: %s" %
                               dialect.name)

        self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert self.Session

        # For database types that support concurrent connections, we
        # create a separate thread pool for connections that promise
        # not to wait on locks.
        if self.no_lock_engine:
            self.NLSession = scoped_session(sessionmaker(
                bind=self.no_lock_engine))
        else:
            self.NLSession = self.Session

    def login(self, config, raw_dsn, pool_options):
        # Default: no password
        passwords = [""]
        pswd_re = re.compile('PASSWORD')

        if config.has_option("database", "password_file"):
            passwd_file = config.get("database", "password_file")
            if passwd_file:
                with open(passwd_file) as f:
                    passwords = [line.strip() for line in f]

                if not passwords:
                    raise AquilonError("Password file %s is empty." %
                                       passwd_file)

        errs = []
        for p in passwords:
            dsn = re.sub(pswd_re, p, raw_dsn)
            self.engine = self.create_engine(config, dsn, **pool_options)
            self.no_lock_engine = self.create_engine(config, dsn,
                                                     **pool_options)

            try:
                connection = self.engine.connect()
                connection.close()
                return
            except DatabaseError as e:
                errs.append(e)

        if errs:
            raise errs.pop()
        else:
            raise AquilonError('Failed to connect to %s' % raw_dsn)

    def get_sequences(self):  # pragma: no cover
        """ return a list of the sequence names from the current databases
            public schema  """

        query = None
        if self.engine.dialect.name == 'oracle':
            query = text("SELECT sequence_name FROM user_sequences")
            return [name for (name, ) in self.engine.execute(query)]
        elif self.engine.dialect.name == 'postgresql':
            query = text("SELECT relname FROM pg_class WHERE relkind = 'S'")
            return [name for (name, ) in self.engine.execute(query)]

    def drop_all_tables_and_sequences(self):  # pragma: no cover
        """ MetaData.drop_all() doesn't play nice with db's that have sequences.
            Your alternative is to call this """
        config = Config()
        if self.engine.dialect.name == 'sqlite':
            dbfile = config.get("database", "dbfile")
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        elif self.engine.dialect.name == 'oracle':
            for table in inspect(self.engine).get_table_names():
                # We can't use bind variables with DDL
                stmt = text('DROP TABLE "%s" CASCADE CONSTRAINTS' %
                            self.engine.dialect.denormalize_name(table))
                self.engine.execute(stmt)
            for seq_name in self.get_sequences():
                seq = Sequence(seq_name)
                seq.drop(bind=self.engine)

            self.engine.execute(text("PURGE RECYCLEBIN"))
        elif self.engine.dialect.name == 'postgresql':
            for table in inspect(self.engine).get_table_names():
                # We can't use bind variables with DDL
                stmt = text('DROP TABLE "%s" CASCADE' % table)
                self.engine.execute(stmt, table=table)
            for seq_name in self.get_sequences():
                seq = Sequence(seq_name)
                seq.drop(bind=self.engine)

            # Should we issue VACUUM?
        else:
            raise ValueError('Can not drop %s databases' %
                             self.engine.dialect.name)
