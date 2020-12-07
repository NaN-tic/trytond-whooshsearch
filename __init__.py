# This file is part whooshsearch module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import whooshsearch

def register():
    Pool.register(
        whooshsearch.WhooshSchema,
        whooshsearch.WhooshField,
        whooshsearch.WhooshWhooshLang,
        whooshsearch.WhooshSchemaGroup,
        whooshsearch.WhooshSchemaStart,
        module='whooshsearch', type_='model')
    Pool.register(
        whooshsearch.WhooshSearch,
        module='whooshsearch', type_='wizard')
