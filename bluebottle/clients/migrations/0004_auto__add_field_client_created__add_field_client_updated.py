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
        # Adding field 'Client.created'
        db.add_column(u'clients_client', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True),
                      keep_default=False)

        # Adding field 'Client.updated'
        db.add_column(u'clients_client', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Client.created'
        db.delete_column(u'clients_client', 'created')

        # Deleting field 'Client.updated'
        db.delete_column(u'clients_client', 'updated')


    models = {
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'client_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'domain_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'schema_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        }
    }

    complete_apps = ['clients']