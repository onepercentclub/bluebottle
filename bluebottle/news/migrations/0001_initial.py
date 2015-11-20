# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'NewsItem'
        db.create_table(u'news_newsitem', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title',
             self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug',
             self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('main_image',
             self.gf('sorl.thumbnail.fields.ImageField')(max_length=100,
                                                         blank=True)),
            ('language',
             self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('status',
             self.gf('django.db.models.fields.CharField')(default='draft',
                                                          max_length=20,
                                                          db_index=True)),
            ('publication_date',
             self.gf('django.db.models.fields.DateTimeField')(null=True,
                                                              db_index=True)),
            ('publication_end_date',
             self.gf('django.db.models.fields.DateTimeField')(db_index=True,
                                                              null=True,
                                                              blank=True)),
            ('allow_comments',
             self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm[settings.AUTH_USER_MODEL])),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('modification_date',
             self.gf('django.db.models.fields.DateTimeField')(
                 default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'news', ['NewsItem'])

    def backwards(self, orm):
        # Deleting model 'NewsItem'
        db.delete_table(u'news_newsitem')

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '80'}),
            'permissions': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'to': u"orm['auth.Permission']", 'symmetrical': 'False',
             'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {
            'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')",
            'unique_together': "((u'content_type', u'codename'),)",
            'object_name': 'Permission'},
            'codename': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [],
                             {'to': u"orm['contenttypes.ContentType']"}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)",
                     'unique_together': "(('app_label', 'model'),)",
                     'object_name': 'ContentType',
                     'db_table': "'django_content_type'"},
            'app_label': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'fluent_contents.placeholder': {
            'Meta': {
            'unique_together': "(('parent_type', 'parent_id', 'slot'),)",
            'object_name': 'Placeholder'},
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_id': (
            'django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [],
                            {'to': u"orm['contenttypes.ContentType']",
                             'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [],
                     {'default': "'m'", 'max_length': '1'}),
            'slot': (
            'django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [],
                      {'max_length': '255', 'blank': 'True'})
        },
        u'news.newsitem': {
            'Meta': {'object_name': 'NewsItem'},
            'allow_comments': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL)}),
            'creation_date': ('django.db.models.fields.DateTimeField', [],
                              {'default': 'datetime.datetime.now',
                               'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': (
            'django.db.models.fields.CharField', [], {'max_length': '5'}),
            'main_image': ('sorl.thumbnail.fields.ImageField', [],
                           {'max_length': '100', 'blank': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [],
                                  {'default': 'datetime.datetime.now',
                                   'blank': 'True'}),
            'publication_date': ('django.db.models.fields.DateTimeField', [],
                                 {'null': 'True', 'db_index': 'True'}),
            'publication_end_date': (
            'django.db.models.fields.DateTimeField', [],
            {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'slug': (
            'django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'draft'", 'max_length': '20',
                        'db_index': 'True'}),
            'title': (
            'django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        settings.AUTH_USER_MODEL.lower(): {
            'Meta': {'object_name': settings.AUTH_USER_MODEL.split('.')[-1]},
            'about': ('django.db.models.fields.TextField', [],
                      {'max_length': '265', 'blank': 'True'}),
            'availability': ('django.db.models.fields.CharField', [],
                             {'max_length': '25', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [],
                          {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [],
                            {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'unique': 'True', 'max_length': '254',
                       'db_index': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [],
                         {'max_length': '50', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'max_length': '30', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [],
                       {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [],
                       {'to': u"orm['auth.Group']", 'symmetrical': 'False',
                        'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [],
                           {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [],
                          {'max_length': '30', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [],
                         {'max_length': '100', 'blank': 'True'}),
            'newsletter': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': (
            'django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [],
                             {'max_length': '50', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [],
                        {'max_length': '100', 'blank': 'True'}),
            'primary_language': (
            'django.db.models.fields.CharField', [], {'max_length': '5'}),
            'share_money': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'share_time_knowledge': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skypename': ('django.db.models.fields.CharField', [],
                          {'max_length': '32', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [],
                        {'max_length': '15', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user_permissions': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'to': u"orm['auth.Permission']", 'symmetrical': 'False',
             'blank': 'True'}),
            'user_type': ('django.db.models.fields.CharField', [],
                          {'default': "'person'", 'max_length': '25'}),
            'username': ('django.db.models.fields.SlugField', [],
                         {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.URLField', [],
                        {'max_length': '200', 'blank': 'True'}),
            'why': ('django.db.models.fields.TextField', [],
                    {'max_length': '265', 'blank': 'True'})
        }
    }

    complete_apps = ['news']
