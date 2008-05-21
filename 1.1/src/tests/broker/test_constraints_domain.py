#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDomainConstraints(TestBrokerCommand):

    def testdeldomainwithhost(self):
        command = "del domain --domain unittest"
        self.badrequesttest(command.split(" "))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "templatesdir"), "unittest")))

    def testverifydeldomainwithhostfailed(self):
        command = "show domain --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Domain: unittest", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

