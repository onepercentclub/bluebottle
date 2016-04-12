# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Statistic'
        db.create_table(u'statistics_statistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='manual', max_length=20, db_index=True)),
            ('sequence', self.gf('django.db.models.fields.IntegerField')()),
            ('value', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')()),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'statistics', ['Statistic'])


    def backwards(self, orm):
        # Deleting model 'Statistic'
        db.delete_table(u'statistics_statistic')


    models = {
        u'statistics.statistic': {
            'Meta': {'object_name': 'Statistic'},
            'active': ('django.db.models.fields.BooleanField', [], {}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20', 'db_index': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['statistics']