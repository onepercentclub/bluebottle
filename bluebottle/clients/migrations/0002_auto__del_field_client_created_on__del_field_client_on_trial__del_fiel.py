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
        # Deleting field 'Client.created_on'
        db.delete_column(u'clients_client', 'created_on')

        # Deleting field 'Client.on_trial'
        db.delete_column(u'clients_client', 'on_trial')

        # Deleting field 'Client.paid_until'
        db.delete_column(u'clients_client', 'paid_until')

        # Adding field 'Client.client_name'
        db.add_column(u'clients_client', 'client_name',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=100),
                      keep_default=False)

    def backwards(self, orm):
        # Adding field 'Client.created_on'
        db.add_column(u'clients_client', 'created_on',
                      self.gf('django.db.models.fields.DateField')(
                          auto_now_add=True, default='', blank=True),
                      keep_default=False)

        # Adding field 'Client.on_trial'
        db.add_column(u'clients_client', 'on_trial',
                      self.gf('django.db.models.fields.BooleanField')(
                          default=''),
                      keep_default=False)

        # Adding field 'Client.paid_until'
        db.add_column(u'clients_client', 'paid_until',
                      self.gf('django.db.models.fields.DateField')(default=''),
                      keep_default=False)

        # Deleting field 'Client.client_name'
        db.delete_column(u'clients_client', 'client_name')

    models = {
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'client_name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'domain_url': ('django.db.models.fields.CharField', [],
                           {'unique': 'True', 'max_length': '128'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'schema_name': ('django.db.models.fields.CharField', [],
                            {'unique': 'True', 'max_length': '63'})
        }
    }

    complete_apps = ['clients']
