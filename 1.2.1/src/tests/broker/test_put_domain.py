#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the put domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPutDomain(TestBrokerCommand):

    def testmakechange(self):
        template = os.path.join(self.scratchdir, "changetest1", "aquilon",
                "archetype", "base.tpl")
        f = open(template)
        try:
            contents = f.readlines()
        finally:
            f.close()
        contents.append("#Added by unittest\n")
        f = open(template, 'w')
        try:
            f.writelines(contents)
        finally:
            f.close()
        self.gitcommand(["commit", "-a", "-m", "added unittest comment"],
                cwd=os.path.join(self.scratchdir, "changetest1"))

    def testputchangetest1domain(self):
        self.ignoreoutputtest(["put", "--domain", "changetest1"],
                env=self.gitenv(),
                cwd=os.path.join(self.scratchdir, "changetest1"))
        self.assert_(os.path.exists(os.path.join(
            self.scratchdir, "changetest1")))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPutDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
