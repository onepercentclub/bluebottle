# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db import connection

from bluebottle.clients.utils import LocalTenant
from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Migration(DataMigration):
    depends_on = (
        ('statistics', '0006_auto__del_field_statistic_language'),
    )

    def forwards(self, orm):
        with LocalTenant(connection.tenant):
            name = connection.tenant.client_name
            if name == 'innovating_justice':
                orm['statistics.Statistic'].objects.create(sequence=1,
                                                           title="Innovations Realized",
                                                           type='projects_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=2,
                                                           title="People Involved",
                                                           type='people_involved',
                                                           active=True)

            if name in ['gent', 'west-friesland']:
                orm['statistics.Statistic'].objects.create(sequence=1,
                                                           title="Projects Online",
                                                           type='projects_online',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=2,
                                                           title="Projects Realized",
                                                           type='projects_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=3,
                                                           title="People Involved",
                                                           type='projects_involved',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=4,
                                                           title="Raised",
                                                           type='donated_total',
                                                           active=True)

            if name in ['onepercent', 'booking']:
                orm['statistics.Statistic'].objects.create(sequence=1,
                                                           title="Projects Online",
                                                           type='projects_online',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=2,
                                                           title="Projects Realized",
                                                           type='projects_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=3,
                                                           title="Tasks Realized",
                                                           type='tasks_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=4,
                                                           title="People Involved",
                                                           type='projects_involved',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=5,
                                                           title="Raised",
                                                           type='donated_total',
                                                           active=True)
            if name == 'kerstactie':
                orm['statistics.Statistic'].objects.create(sequence=1, title="Projects Online", type='projects_online', active=True)
                orm['statistics.Statistic'].objects.create(sequence=2,
                                                           title="Projects Realized",
                                                           type='projects_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=3,
                                                           title="People Involved",
                                                           type='projects_involved',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=4,
                                                           title="Raised",
                                                           type='donated_total',
                                                           active=True)

            if name == 'dll':
                orm['statistics.Statistic'].objects.create(sequence=1,
                                                           title="Projects Online",
                                                           type='projects_online',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=2,
                                                           title="Projects Realized",
                                                           type='projects_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=3,
                                                           title="Tasks Realized",
                                                           type='tasks_realized',
                                                           active=True)
                orm['statistics.Statistic'].objects.create(sequence=4,
                                                           title="People Involved",
                                                           type='projects_involved',
                                                           active=True)

            if name == 'abn':
                pass

            if name == 'accenture':
                pass

            if name == 'rabobank':
                pass

            if name == 'impact-booster':
                pass

            if name == 'rooftop-revolution':
                pass

            if name == 'startsomething':
                pass


    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'statistics.statistic': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Statistic'},
            'active': ('django.db.models.fields.BooleanField', [], {}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title_nl': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['homepage']
    symmetrical = True
