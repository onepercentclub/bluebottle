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
        # Adding model 'Client'
        db.create_table(u'clients_client', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain_url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('schema_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=63)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('paid_until', self.gf('django.db.models.fields.DateField')()),
            ('on_trial', self.gf('django.db.models.fields.BooleanField')()),
            ('created_on', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'clients', ['Client'])


    def backwards(self, orm):
        # Deleting model 'Client'
        db.delete_table(u'clients_client')


    models = {
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'created_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'on_trial': ('django.db.models.fields.BooleanField', [], {}),
            'paid_until': ('django.db.models.fields.DateField', [], {}),
            'schema_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63'})
        }
    }

    complete_apps = ['clients']