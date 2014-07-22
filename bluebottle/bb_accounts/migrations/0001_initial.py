# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TimeAvailable'
        db.create_table(u'bb_accounts_timeavailable', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'bb_accounts', ['TimeAvailable'])


    def backwards(self, orm):
        # Deleting model 'TimeAvailable'
        db.delete_table(u'bb_accounts_timeavailable')


    models = {
        u'bb_accounts.timeavailable': {
            'Meta': {'ordering': "['type']", 'object_name': 'TimeAvailable'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['bb_accounts']