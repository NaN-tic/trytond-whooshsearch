# This file is part of the whooshsearch module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class WhooshSearchTestCase(ModuleTestCase):
    'Test Whoosh Search module'
    module = 'whooshsearch'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        WhooshSearchTestCase))
    return suite
