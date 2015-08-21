# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ('fluent_contents', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'PictureItem'
        db.create_table('contentitem_contentplugins_pictureitem', (
            ('contentitem_ptr',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['fluent_contents.ContentItem'], unique=True,
                 primary_key=True)),
            ('image',
             self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
            ('align',
             self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('contentplugins', ['PictureItem'])

    def backwards(self, orm):
        # Deleting model 'PictureItem'
        db.delete_table('contentitem_contentplugins_pictureitem')

    models = {
        'contentplugins.pictureitem': {
            'Meta': {'ordering': "('placeholder', 'sort_order')",
                     'object_name': 'PictureItem',
                     'db_table': "'contentitem_contentplugins_pictureitem'",
                     '_ormbases': ['fluent_contents.ContentItem']},
            'align': (
            'django.db.models.fields.CharField', [], {'max_length': '50'}),
            'contentitem_ptr': (
            'django.db.models.fields.related.OneToOneField', [],
            {'to': "orm['fluent_contents.ContentItem']", 'unique': 'True',
             'primary_key': 'True'}),
            'image': (
            'sorl.thumbnail.fields.ImageField', [], {'max_length': '100'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)",
                     'unique_together': "(('app_label', 'model'),)",
                     'object_name': 'ContentType',
                     'db_table': "'django_content_type'"},
            'app_label': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'fluent_contents.contentitem': {
            'Meta': {'ordering': "('placeholder', 'sort_order')",
                     'object_name': 'ContentItem'},
            'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_id': (
            'django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [],
                            {'to': "orm['contenttypes.ContentType']"}),
            'placeholder': ('django.db.models.fields.related.ForeignKey', [],
                            {'related_name': "'contentitems'", 'null': 'True',
                             'on_delete': 'models.SET_NULL',
                             'to': "orm['fluent_contents.Placeholder']"}),
            'polymorphic_ctype': (
            'django.db.models.fields.related.ForeignKey', [],
            {'related_name': "'polymorphic_fluent_contents.contentitem_set'",
             'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [],
                           {'default': '1', 'db_index': 'True'})
        },
        'fluent_contents.placeholder': {
            'Meta': {
            'unique_together': "(('parent_type', 'parent_id', 'slot'),)",
            'object_name': 'Placeholder'},
            'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_id': (
            'django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [],
                            {'to': "orm['contenttypes.ContentType']",
                             'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [],
                     {'default': "'m'", 'max_length': '1'}),
            'slot': (
            'django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [],
                      {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['contentplugins']
