# This file is part whooshsearch module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Eval, PYSONEncoder, Id
from trytond.config import config
from whoosh import index
from whoosh.fields import Schema, ID as wID, BOOLEAN as wBOOLEAN, \
    NUMERIC as wNUMERIC, TEXT as wTEXT, DATETIME as wDATETIME
from whoosh.qparser import MultifieldParser
from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map
import os
import shutil
import logging
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['WhooshSchema', 'WhooshField', 'WhooshWhooshLang', 'WhooshSchemaGroup',
    'WhooshSchemaStart', 'WhooshSearch']

logger = logging.getLogger(__name__)
EXCLUDE_FIELDS = ['property', 'sha', 'binary', 'one2many', 'one2one',
    'timestamp', 'time', 'reference']
FIELD2WHOOSH = {
    'boolean': wBOOLEAN,
    'integer': wNUMERIC,
    'biginteger': wNUMERIC,
    'char': wTEXT,
    'text': wTEXT,
    'float': wNUMERIC,
    'numeric': wNUMERIC,
    'date': wDATETIME,
    'datetime': wDATETIME,
    'selection': wTEXT,
    'many2one': wTEXT,
    'many2many': wTEXT,
    'function': wTEXT,
    }


class WhooshSchema(ModelSQL, ModelView):
    'Whoosh Schema'
    __name__ = 'whoosh.schema'
    name = fields.Char('Name', required=True, translate=True)
    slug = fields.Char('Slug', required=True,
        help='Schema directory name: az09')
    model = fields.Many2One('ir.model', 'Model', required=True)
    domain = fields.Char('Domain')
    fields_ = fields.One2Many('whoosh.field', 'schema', 'Fields')
    langs = fields.Many2Many('whoosh.schema-whoosh.lang',
        'schema', 'lang', 'Langs',
        domain=[('translatable', '=', True)])
    active = fields.Boolean('Active', select=True)
    debug = fields.Boolean('Debug')
    schema_groups = fields.Many2Many('whoosh.schema-res.group', 'schema',
        'group', 'Groups',
        states={
            'invisible': ~Eval('groups', []).contains(Id('res', 'group_admin')
                ),
            },
        help='User groups that will be able to use this schema.')

    @classmethod
    def __setup__(cls):
        super(WhooshSchema, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints = [
            ('slug_uniq', Unique(t, t.slug),
                'The slug of the whoosh schema must be unique.')
            ]
        cls._buttons.update({
            'create_schema': {},
            'remove_schema': {},
            'generate_index': {},
            })

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_langs():
        Lang = Pool().get('ir.lang')

        langs = Lang.search([
            ('translatable', '=', True),
            ])
        if len(langs) > 1:
            return [l.id for l in langs]
        return None

    @staticmethod
    def _remove_schema(schemas):
        for schema in schemas:
            db_name = Transaction().database.name
            schema_dir = os.path.join(config.get('database', 'path'),
                db_name, 'whoosh', schema.slug)
            try:
                shutil.rmtree(schema_dir)
                logger.info(
                    'Remove schema directory "%s"' % schema.slug)
            except:
                logger.info(
                    'Not remove schema directory "%s"' % schema.slug)

    @classmethod
    @ModelView.button
    def create_schema(cls, schemas):
        '''Create Schemas for each model

        Whoosh project path directory:
        DATABASEPATH/whoosh/SCHEMA-SLUG/LANG-CODE.lower()
        '''
        for schema in schemas:
            db_name = Transaction().database.name
            schema_dir = os.path.join(config.get('database', 'path'),
                db_name, 'whoosh', schema.slug)

            if not os.path.exists(schema_dir):
                os.makedirs(schema_dir)

            langs = [l.code.lower() for l in schema.langs] \
                if schema.langs \
                else [Transaction().context.get('language').lower()]

            for lang in langs:
                schema_lang_dir = os.path.join(schema_dir, lang)
                if not os.path.exists(schema_lang_dir):
                    os.makedirs(schema_lang_dir)

                sc = {}
                sc['id'] = wID(stored=True, unique=True)
                for f in schema.fields_:
                    field = f.field

                    if field.ttype in EXCLUDE_FIELDS:
                        continue

                    options = {'analyzer': None}
                    if f.stored:
                        options['stored'] = True
                    if f.unique:
                        options['unique'] = True
                    if f.stemming:
                        options['analyzer'] = StemmingAnalyzer()
                    if f.ignore_accents:
                        if options['analyzer']:
                            options['analyzer'] |= CharsetFilter(accent_map)
                        else:
                            options['analyzer'] = CharsetFilter(accent_map)

                    field_type = FIELD2WHOOSH.get(field.ttype)
                    sc[f.name] = field_type(**options)

                if schema.debug:
                    logger.info(sc)

                schema_obj = Schema(**sc)
                index.create_in(schema_lang_dir, schema_obj)

            logger.info(
                'Created/Updated %s Schemas' % schema.slug)

    @classmethod
    @ModelView.button
    def remove_schema(cls, schemas):
        '''Remove schema directory'''
        cls._remove_schema(schemas)

    @classmethod
    @ModelView.button
    def generate_index(cls, schemas):
        '''Generate indexing data each schema'''
        for schema in schemas:
            logger.info('Start schema %s' % schema.slug)

            db_name = Transaction().database.name
            schema_dir = os.path.join(config.get('database', 'path'),
                db_name, 'whoosh', schema.slug)

            if not os.path.exists(schema_dir):
                logger.error(
                    'Schema directory "%s" not exist' % schema.slug)
                continue

            langs = [l.code.lower() for l in schema.langs] \
                if schema.langs \
                else [Transaction().context.get('language').lower()]

            for lang in langs:
                schema_lang_dir = os.path.join(schema_dir, lang)
                if not os.path.exists(schema_lang_dir):
                    logger.error(
                        'Schema lang directory "%s" not exist' % lang)
                    continue

                if schema.debug:
                    logger.info(schema_lang_dir)

                ix = index.open_dir(schema_lang_dir)
                writer = ix.writer()

                Model = Pool().get(schema.model.model)
                with Transaction().set_context(language=lang):
                    records = Model.search(
                        domain=eval(schema.domain) if schema.domain else [],
                        )

                for record in records:
                    data = {}
                    data['id'] = u'%s' % str(record.id)
                    for f in schema.fields_:
                        value = getattr(record, f.field.name)
                        if f.field.ttype == 'many2one':
                            value = value.rec_name if value else None
                        if f.field.ttype == 'many2many':
                            value = ", ".join([v.rec_name for v in value if v])
                        data[f.name] = u'%s' % value

                    if schema.debug:
                        logger.info('%s' % data)

                    writer.update_document(**data)

                writer.commit()
                logger.info(
                    'Total Schema "%s" - "%s": %s' % (schema.slug, lang, ix.doc_count()))

            logger.info('End indexing schema "%s"' % schema.slug)

    @classmethod
    def copy(cls, schemas, default=None):
        new_schemas = []
        for schema in schemas:
            default['slug'] = '%s-copy' % schema.slug
            new_schema, = super(WhooshSchema, cls).copy([schema], default=default)
            new_schemas.append(new_schema)
        return new_schemas

    @classmethod
    def delete(cls, schemas):
        cls._remove_schema(schemas)
        super(WhooshSchema, cls).delete(schemas)


class WhooshField(ModelSQL, ModelView):
    'Whoosh Field'
    __name__ = 'whoosh.field'
    schema = fields.Many2One('whoosh.schema', 'Schema', required=True,
        ondelete='CASCADE')
    name = fields.Char('Name', required=True,
        help='Field name in Whoosh ("name", "content", "slug"...')
    field = fields.Many2One('ir.model.field', 'Field', required=True,
        domain=[('model', '=', Eval('_parent_schema', {}).get('model'))])
    stored = fields.Boolean('Stored')
    unique = fields.Boolean('Unique')
    stemming = fields.Boolean('Stemming')
    ignore_accents = fields.Boolean('Ignore Accents')
    parser = fields.Boolean('Parser',
        help='Use field to Multifield Parser.')
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_stored():
        return True

    @staticmethod
    def default_active():
        return True

    @fields.depends('field', 'name')
    def on_change_field(self):
        self.name = None
        if self.field:
            self.name = self.field.name


class EmptyStateAction(StateAction):
    def __init__(self):
        super(EmptyStateAction, self).__init__(None)

    def get_action(self):
        return {}


class WhooshSchemaStart(ModelView):
    'Whoosh Schema Start'
    __name__ = 'whoosh.schema.start'
    schema = fields.Many2One('whoosh.schema', 'Schema', required=True,
        domain=[
            ['OR',
                ('schema_groups', 'in',
                    Eval('context', {}).get('groups', [])),
                ('schema_groups', '=', None),
            ],
            ])
    q = fields.Char('Search', required=True,
        help='Concanate words with "+" to AND or "-" to NOT')


class WhooshSearch(Wizard):
    'Whoosh Search'
    __name__ = 'whoosh.search'
    start = StateView('whoosh.schema.start',
        'whooshsearch.whoosh_schema_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Search', 'open_', 'tryton-ok', default=True),
            ])
    open_ = EmptyStateAction()

    def do_open_(self, action):
        schema = self.start.schema
        q = self.start.q

        db_name = Transaction().database.name
        lang = Transaction().context.get('language').lower()

        schema_dir = os.path.join(config.get('database', 'path'),
            db_name, 'whoosh', schema.slug, lang)

        if not os.path.exists(schema_dir):
            raise UserError(gettext('whooshsearch.msg_not_schema_dir',
                slug=schema.slug, lang=lang))

        fields = []
        for field in schema.fields_:
            if field.parser:
                fields.append(field.name)
        if not fields:
            raise UserError(gettext('whooshsearch.msg_not_fields',
                slug=schema.slug))

        ix = index.open_dir(schema_dir)

        query = q.replace('+', ' AND ').replace('-', ' NOT ')
        query = MultifieldParser(fields, ix.schema).parse(query)

        with ix.searcher() as s:
            results = s.search(query)
            res = [result.get('id') for result in results]

        model = schema.model
        model_model = model.model

        domain = [('id', 'in', res)]

        domain = PYSONEncoder().encode(domain)
        context = {}
        return {
            'id': -1,
            'name': '%s - %s (%s)' % (schema.name, model.name, q),
            'model': model_model,
            'res_model': model_model,
            'type': 'ir.action.act_window',
            'context_model': None,
            'context_domain': None,
            'pyson_domain': domain,
            'pyson_context': context,
            'pyson_order': '[]',
            'pyson_search_value': '[]',
            'domains': [],
            }, {}


class WhooshWhooshLang(ModelSQL):
    'Whoosh Schema - Whoosh Lang'
    __name__ = 'whoosh.schema-whoosh.lang'
    _table = 'whoosh_schema_lang_rel'
    schema = fields.Many2One('whoosh.schema', 'Schema', ondelete='CASCADE',
        required=True, select=True)
    lang = fields.Many2One('ir.lang', 'Language',
        ondelete='CASCADE', required=True, select=True)


class WhooshSchemaGroup(ModelSQL):
    'Whoosh Schema - Group'
    __name__ = 'whoosh.schema-res.group'
    schema = fields.Many2One('whoosh.schema', 'Schema', required=True)
    group = fields.Many2One('res.group', 'Group', required=True)
