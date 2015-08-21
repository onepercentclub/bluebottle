# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Migration(DataMigration):
    def forwards(self, orm):
        "Write your forwards methods here."
        orm['bb_projects.ProjectPhase'].objects.filter(slug='campaign').update(
            editable=False)
        orm['bb_projects.ProjectPhase'].objects.filter(
            slug='done-complete').update(editable=False)

    def backwards(self, orm):
        "Write your backwards methods here."
        orm['bb_projects.ProjectPhase'].objects.filter(slug='campaign').update(
            editable=True)
        orm['bb_projects.ProjectPhase'].objects.filter(
            slug='done-complete').update(editable=True)

    models = {
        u'bb_projects.projectphase': {
            'Meta': {'ordering': "['sequence']", 'object_name': 'ProjectPhase'},
            'active': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [],
                            {'max_length': '400', 'blank': 'True'}),
            'editable': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'owner_editable': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sequence': (
            'django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '200'}),
            'viewable': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'bb_projects.projecttheme': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProjectTheme'},
            'description': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [],
                        {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['bb_projects']
    symmetrical = True
