# This file is part whooshsearch module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .whooshsearch import *

def register():
    Pool.register(
        WhooshSchema,
        WhooshField,
        WhooshWhooshLang,
        WhooshSchemaGroup,
        WhooshSchemaStart,
        module='whooshsearch', type_='model')
    Pool.register(
        WhooshSearch,
        module='whooshsearch', type_='wizard')
