# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.test import TestCase

from lizard_waterbalance.models import Polder

class PolderTestSuite(TestCase):

    def test_a(self):
        """We can construct a polder."""
        polder = Polder()
        # If I get to here, the previous statement resulted in a new polder
        # and that was what I wanted to know.

        # If we do not use the new polder, pyflakes will file a complaint about
        # complain about that. So to keep pyflakes happy, we test that the
        # is not None
        self.assertTrue(polder != None)

