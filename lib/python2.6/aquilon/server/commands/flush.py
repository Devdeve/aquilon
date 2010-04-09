# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq flush`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Service, Machine, Domain, Personality, Cluster
from aquilon.server.templates.personality import PlenaryPersonality
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.service import (PlenaryService,
                                              PlenaryServiceInstance)
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.domain import compileLock, compileRelease
from aquilon.exceptions_ import PartialError, IncompleteError


class CommandFlush(BrokerCommand):

    def render(self, session, logger, user, 
               services, personalities, machines, clusters, hosts, all,
               **arguments):
        success = []
        failed = []
        written = 0

        try:
            compileLock(logger=logger)

            if services or all:
                logger.client_info("flushing services")
                for dbservice in session.query(Service).all():
                    try:
                        plenary_info = PlenaryService(dbservice)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        failed.append("service %s failed: %s" % (dbservice.name, e))
                        continue

                    for dbinst in dbservice.instances:
                        try:
                            plenary_info = PlenaryServiceInstance(dbservice, dbinst)
                            written += plenary_info.write(locked=True)
                        except Exception, e:
                            failed.append("service %s instance %s failed: %s" % (dbservice.name, dbinst.name, e))
                            continue

            if personalities or all:
                logger.client_info("flushing personalities")
                for persona in session.query(Personality).all():
                    try:
                        plenary_info = PlenaryPersonality(persona)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        failed.append("personality %s failed: %s" %
                                      (persona.name, e))
                        continue

            if machines or all:
                logger.client_info("flushing machines")
                for machine in session.query(Machine).all():
                    try:
                        plenary_info = PlenaryMachineInfo(machine)
                        written += plenary_info.write(locked=True)
                    except Exception, e:
                        label = machine.name
                        if machine.host:
                            label = "%s (host: %s)" % (machine.name,
                                                       machine.host.fqdn)
                        failed.append("machine %s failed: %s" % (label, e))
                        continue

            if hosts or all:
                logger.client_info("flushing hosts")
                for d in session.query(Domain).all():
                    for h in d.hosts:
                        if not h.archetype.is_compileable:
                            continue
                        try:
                            plenary_host = PlenaryHost(h)
                            written += plenary_host.write(locked=True)
                        except IncompleteError, e:
                            pass
                            #logger.client_info("Not flushing host: %s" % e)
                        except Exception, e:
                            failed.append("host %s in domain %s failed: %s" %(h.fqdn,d.name,e))

            if clusters or all:
                logger.client_info("flushing clusters")
                for clus in session.query(Cluster).all():
                    try:
                        plenary = PlenaryCluster(clus)
                        written += plenary.write(locked=True)
                    except Exception, e:
                        failed.append("%s cluster %s failed: %s" %
                                      (clus.cluster_type, clus.name, e))

            # written + len(failed) isn't actually the total that should
            # have been done, but it's the easiest to implement for this
            # count and should be reasonably close... :)
            logger.client_info("flushed %d/%d templates" %
                               (written, written + len(failed)))
            if failed:
                raise PartialError(success, failed)

        finally:
            compileRelease(logger=logger)

        return