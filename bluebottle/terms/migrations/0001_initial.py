# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Terms'
        db.create_table(u'terms_terms', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['members.Member'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('contents',
             self.gf('django.db.models.fields.CharField')(max_length=500000)),
            ('version',
             self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal(u'terms', ['Terms'])

        # Adding model 'TermsAgreement'
        db.create_table(u'terms_termsagreement', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['members.Member'])),
            ('terms', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['terms.Terms'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'terms', ['TermsAgreement'])

    def backwards(self, orm):
        # Deleting model 'Terms'
        db.delete_table(u'terms_terms')

        # Deleting model 'TermsAgreement'
        db.delete_table(u'terms_termsagreement')

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
            'about': ('django.db.models.fields.TextField', [],
                      {'max_length': '265', 'blank': 'True'}),
            'available_time': ('django.db.models.fields.CharField', [],
                               {'max_length': '50', 'null': 'True',
                                'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [],
                          {'null': 'True', 'blank': 'True'}),
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
            'facebook': ('django.db.models.fields.CharField', [],
                         {'max_length': '50', 'blank': 'True'}),
            'favourite_countries': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'symmetrical': 'False', 'to': u"orm['geo.Country']",
             'null': 'True', 'blank': 'True'}),
            'favourite_themes': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'symmetrical': 'False', 'to': u"orm['bb_projects.ProjectTheme']",
             'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'max_length': '100', 'blank': 'True'}),
            'full_name': (
            'django.db.models.fields.CharField', [], {'max_length': '255'}),
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
                          {'max_length': '100', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [],
                         {'max_length': '100', 'blank': 'True'}),
            'my_destinations': (
            'django.db.models.fields.related.ManyToManyField', [],
            {'blank': 'True', 'related_name': "'my_destination_set'",
             'null': 'True', 'symmetrical': 'False',
             'to': u"orm['offices.Office']"}),
            'newsletter': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'office': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['offices.Office']", 'null': 'True',
                        'blank': 'True'}),
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
            'skills': ('django.db.models.fields.related.ManyToManyField', [],
                       {'symmetrical': 'False', 'to': "orm['tasks.Skill']",
                        'null': 'True',
                        'blank': 'True'}),
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
        },
        u'offices.office': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Office'},
            'city': ('django.db.models.fields.CharField', [],
                     {'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [],
                        {'to': u"orm['geo.Country']"}),
            'description': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'Active'", 'max_length': "'30'"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {
            'related_name': "u'taggit_taggeditem_tagged_items'",
            'to': u"orm['contenttypes.ContentType']"}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': (
            'django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [],
                    {'related_name': "u'taggit_taggeditem_items'",
                     'to': u"orm['taggit.Tag']"})
        },
        u'tasks.skill': {
            'Meta': {'ordering': "('id',)",
                     'object_name': 'Skill'},
            'description': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [],
                        {'unique': 'True', 'max_length': '100'})
        },
        u'terms.terms': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Terms'},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': "orm['members.Member']"}),
            'contents': (
            'django.db.models.fields.CharField', [], {'max_length': '500000'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'version': (
            'django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        u'terms.termsagreement': {
            'Meta': {'object_name': 'TermsAgreement'},
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'terms': ('django.db.models.fields.related.ForeignKey', [],
                      {'to': u"orm['terms.Terms']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': "orm['members.Member']"})
        }
    }

    complete_apps = ['terms']
