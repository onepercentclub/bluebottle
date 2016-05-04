# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table(u'categories_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('image', self.gf('bluebottle.utils.fields.ImageField')(max_length=255, null=True, blank=True)),
            ('image_logo', self.gf('bluebottle.utils.fields.ImageField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'categories', ['Category'])


    def backwards(self, orm):
        # Deleting model 'Category'
        db.delete_table(u'categories_category')


    models = {
        u'categories.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('bluebottle.utils.fields.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'image_logo': ('bluebottle.utils.fields.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['categories']