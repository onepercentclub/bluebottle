# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'TimeAvailable'
        db.delete_table(u'bb_accounts_timeavailable')


    def backwards(self, orm):
        # Adding model 'TimeAvailable'
        db.create_table(u'bb_accounts_timeavailable', (
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'bb_accounts', ['TimeAvailable'])


    models = {
        
    }

    complete_apps = ['bb_accounts']