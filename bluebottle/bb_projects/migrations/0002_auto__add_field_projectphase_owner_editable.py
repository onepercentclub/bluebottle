# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ProjectPhase.owner_editable'
        db.add_column(u'bb_projects_projectphase', 'owner_editable',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ProjectPhase.owner_editable'
        db.delete_column(u'bb_projects_projectphase', 'owner_editable')


    models = {
        u'{0}.projectphase'.format(settings.PROJECTS_PROJECT_MODEL.split('.')[0]): {
            'Meta': {'ordering': "['sequence']", 'object_name': 'ProjectPhase'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'owner_editable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'viewable': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'{0}.projecttheme'.format(settings.PROJECTS_PROJECT_MODEL.split('.')[0]): {
            'Meta': {'ordering': "['name']", 'object_name': 'ProjectTheme'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['bb_projects']