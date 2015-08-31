# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'UserAddress'
        db.create_table('members_useraddress', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line1',
             self.gf('django.db.models.fields.CharField')(max_length=100,
                                                          blank=True)),
            ('line2',
             self.gf('django.db.models.fields.CharField')(max_length=100,
                                                          blank=True)),
            ('city',
             self.gf('django.db.models.fields.CharField')(max_length=100,
                                                          blank=True)),
            ('state',
             self.gf('django.db.models.fields.CharField')(max_length=100,
                                                          blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['geo.Country'], null=True, blank=True)),
            ('postal_code',
             self.gf('django.db.models.fields.CharField')(max_length=20,
                                                          blank=True)),
            ('address_type',
             self.gf('django.db.models.fields.CharField')(default='primary',
                                                          max_length=10,
                                                          blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(
                related_name='address', unique=True, to=orm['members.Member'])),
        ))
        db.send_create_signal(u'bb_accounts', ['UserAddress'])

    def backwards(self, orm):
        # Deleting model 'UserAddress'
        db.delete_table('members_useraddress')

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
        u'bb_accounts.useraddress': {
            'Meta': {'object_name': 'UserAddress',
                     'db_table': "'members_useraddress'"},
            'address_type': ('django.db.models.fields.CharField', [],
                             {'default': "'primary'", 'max_length': '10',
                              'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [],
                     {'max_length': '100', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [],
                        {'to': u"orm['geo.Country']", 'null': 'True',
                         'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line1': ('django.db.models.fields.CharField', [],
                      {'max_length': '100', 'blank': 'True'}),
            'line2': ('django.db.models.fields.CharField', [],
                      {'max_length': '100', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [],
                            {'max_length': '20', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [],
                      {'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [],
                     {'related_name': "'address'", 'unique': 'True',
                      'to': u"orm['members.Member']"})
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
        u'geo.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country'},
            'alpha2_code': ('django.db.models.fields.CharField', [],
                            {'max_length': '2', 'blank': 'True'}),
            'alpha3_code': ('django.db.models.fields.CharField', [],
                            {'max_length': '3', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'}),
            'oda_recipient': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [],
                          {'to': u"orm['geo.SubRegion']"})
        },
        u'geo.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'})
        },
        u'geo.subregion': {
            'Meta': {'ordering': "['name']", 'object_name': 'SubRegion'},
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['geo.Region']"})
        },
        u'members.member': {
            'Meta': {'object_name': 'Member'},
            'about_me': ('django.db.models.fields.TextField', [],
                         {'max_length': '265', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [],
                          {'null': 'True', 'blank': 'True'}),
            'campaign_notifications': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [],
                            {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'disable_token': ('django.db.models.fields.CharField', [],
                              {'max_length': '32', 'null': 'True',
                               'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'unique': 'True', 'max_length': '254',
                       'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'max_length': '100', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [],
                       {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [],
                       {'symmetrical': 'False', 'related_name': "u'user_set'",
                        'blank': 'True', 'to': u"orm['auth.Group']"}),
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
                          {'max_length': '100', 'blank': 'True'}),
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
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user_permissions': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'symmetrical': 'False', 'related_name': "u'user_set'",
             'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'user_type': ('django.db.models.fields.CharField', [],
                          {'default': "'person'", 'max_length': '25'}),
            'username': ('django.db.models.fields.SlugField', [],
                         {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['bb_accounts']
