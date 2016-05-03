# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db import connection

from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant


class Migration(DataMigration):

    def forwards(self, orm):
        with LocalTenant(connection.tenant):
            for statistic in orm['statistics.Statistic'].objects.all():
                if statistic.title_en:
                    statistic_en = orm['statistics.Statistic'].objects.create(
                        title=statistic.title_en,
                        language='en',
                        type=statistic.type,
                        sequence=statistic.sequence,
                        value=statistic.value,
                        active=statistic.active
                    )
                if statistic.title_nl:
                    statistic_nl = orm['statistics.Statistic'].objects.create(
                        title=statistic.title_nl,
                        language='nl',
                        type=statistic.type,
                        sequence=statistic.sequence,
                        value=statistic.value,
                        active=statistic.active
                    )
                statistic.delete()


    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'statistics.statistic': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statistic'},
            'active': ('django.db.models.fields.BooleanField', [], {}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'title_nl': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['statistics']
    symmetrical = True
