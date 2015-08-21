# -*- coding: utf-8 -*-
# Generated with bb_schemamigration
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding unique constraint on 'Client', fields ['client_name']
        db.create_unique(u'clients_client', ['client_name'])

    def backwards(self, orm):
        # Removing unique constraint on 'Client', fields ['client_name']
        db.delete_unique(u'clients_client', ['client_name'])

    models = {
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'client_name': ('django.db.models.fields.CharField', [],
                            {'unique': 'True', 'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'domain_url': ('django.db.models.fields.CharField', [],
                           {'unique': 'True', 'max_length': '128'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'schema_name': ('django.db.models.fields.CharField', [],
                            {'unique': 'True', 'max_length': '63'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        }
    }

    complete_apps = ['clients']
