# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Statistic'
        db.delete_table(u'statistics_statistic')


    def backwards(self, orm):
        # Adding model 'Statistic'
        db.create_table(u'statistics_statistic', (
            ('hours_spent', self.gf('django.db.models.fields.IntegerField')()),
            ('countries', self.gf('django.db.models.fields.IntegerField')()),
            ('lives_changed', self.gf('django.db.models.fields.IntegerField')()),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('projects', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'statistics', ['Statistic'])


    models = {
        
    }

    complete_apps = ['statistics']