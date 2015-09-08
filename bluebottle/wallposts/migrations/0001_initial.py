# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Wallpost'
        db.create_table(u'wallposts_wallpost', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype',
             self.gf('django.db.models.fields.related.ForeignKey')(
                 related_name=u'polymorphic_wallposts.wallpost_set', null=True,
                 to=orm['contenttypes.ContentType'])),
            ('author',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='wallpost_wallpost',
                                                                   null=True,
                                                                   to=orm[
                                                                       settings.AUTH_USER_MODEL])),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm[settings.AUTH_USER_MODEL], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('deleted',
             self.gf('django.db.models.fields.DateTimeField')(null=True,
                                                              blank=True)),
            ('ip_address',
             self.gf('django.db.models.fields.IPAddressField')(default=None,
                                                               max_length=15,
                                                               null=True,
                                                               blank=True)),
            ('content_type',
             self.gf('django.db.models.fields.related.ForeignKey')(
                 related_name='content_type_set_for_wallpost',
                 to=orm['contenttypes.ContentType'])),
            ('object_id',
             self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'wallposts', ['Wallpost'])

        # Adding model 'MediaWallpost'
        db.create_table(u'wallposts_mediawallpost', (
            (u'wallpost_ptr',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['wallposts.Wallpost'], unique=True, primary_key=True)),
            ('title',
             self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('text', self.gf('django.db.models.fields.TextField')(default='',
                                                                  max_length=300,
                                                                  blank=True)),
            ('video_url',
             self.gf('django.db.models.fields.URLField')(default='',
                                                         max_length=100,
                                                         blank=True)),
        ))
        db.send_create_signal(u'wallposts', ['MediaWallpost'])

        # Adding model 'MediaWallpostPhoto'
        db.create_table(u'wallposts_mediawallpostphoto', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mediawallpost',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='photos',
                                                                   null=True,
                                                                   to=orm[
                                                                       'wallposts.MediaWallpost'])),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(
                max_length=100)),
            ('deleted',
             self.gf('django.db.models.fields.DateTimeField')(null=True,
                                                              blank=True)),
            ('ip_address',
             self.gf('django.db.models.fields.IPAddressField')(default=None,
                                                               max_length=15,
                                                               null=True,
                                                               blank=True)),
            ('author',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='mediawallpostphoto_wallpost_photo',
                                                                   null=True,
                                                                   to=orm[
                                                                       settings.AUTH_USER_MODEL])),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm[settings.AUTH_USER_MODEL], null=True, blank=True)),
        ))
        db.send_create_signal(u'wallposts', ['MediaWallpostPhoto'])

        # Adding model 'TextWallpost'
        db.create_table(u'wallposts_textwallpost', (
            (u'wallpost_ptr',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['wallposts.Wallpost'], unique=True, primary_key=True)),
            ('text',
             self.gf('django.db.models.fields.TextField')(max_length=300)),
        ))
        db.send_create_signal(u'wallposts', ['TextWallpost'])

        # Adding model 'SystemWallpost'
        db.create_table(u'wallposts_systemwallpost', (
            (u'wallpost_ptr',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['wallposts.Wallpost'], unique=True, primary_key=True)),
            ('text',
             self.gf('django.db.models.fields.TextField')(max_length=300,
                                                          blank=True)),
            ('related_type',
             self.gf('django.db.models.fields.related.ForeignKey')(
                 to=orm['contenttypes.ContentType'])),
            ('related_id',
             self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'wallposts', ['SystemWallpost'])

        # Adding model 'Reaction'
        db.create_table(u'wallposts_reaction', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='wallpost_reactions',
                to=orm[settings.AUTH_USER_MODEL])),
            ('editor',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='+',
                                                                   null=True,
                                                                   to=orm[
                                                                       settings.AUTH_USER_MODEL])),
            ('text',
             self.gf('django.db.models.fields.TextField')(max_length=300)),
            ('wallpost', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='reactions', to=orm['wallposts.Wallpost'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('deleted',
             self.gf('django.db.models.fields.DateTimeField')(null=True,
                                                              blank=True)),
            ('ip_address',
             self.gf('django.db.models.fields.IPAddressField')(default=None,
                                                               max_length=15,
                                                               null=True,
                                                               blank=True)),
        ))
        db.send_create_signal(u'wallposts', ['Reaction'])

    def backwards(self, orm):
        # Deleting model 'Wallpost'
        db.delete_table(u'wallposts_wallpost')

        # Deleting model 'MediaWallpost'
        db.delete_table(u'wallposts_mediawallpost')

        # Deleting model 'MediaWallpostPhoto'
        db.delete_table(u'wallposts_mediawallpostphoto')

        # Deleting model 'TextWallpost'
        db.delete_table(u'wallposts_textwallpost')

        # Deleting model 'SystemWallpost'
        db.delete_table(u'wallposts_systemwallpost')

        # Deleting model 'Reaction'
        db.delete_table(u'wallposts_reaction')

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
        u'bb_accounts.timeavailable': {
            'Meta': {'ordering': "['type']", 'object_name': 'TimeAvailable'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [],
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
        settings.AUTH_USER_MODEL.lower(): {
            'Meta': {'object_name': settings.AUTH_USER_MODEL.split('.')[-1]},
            'about': ('django.db.models.fields.TextField', [],
                      {'max_length': '265', 'blank': 'True'}),
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
            'time_available': ('django.db.models.fields.related.ForeignKey', [],
                               {'to': u"orm['bb_accounts.TimeAvailable']",
                                'null': 'True', 'blank': 'True'}),
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
        u'wallposts.mediawallpost': {
            'Meta': {'ordering': "('created',)", 'object_name': 'MediaWallpost',
                     '_ormbases': [u'wallposts.Wallpost']},
            'text': ('django.db.models.fields.TextField', [],
                     {'default': "''", 'max_length': '300', 'blank': 'True'}),
            'title': (
            'django.db.models.fields.CharField', [], {'max_length': '60'}),
            'video_url': ('django.db.models.fields.URLField', [],
                          {'default': "''", 'max_length': '100',
                           'blank': 'True'}),
            u'wallpost_ptr': (
            'django.db.models.fields.related.OneToOneField', [],
            {'to': u"orm['wallposts.Wallpost']", 'unique': 'True',
             'primary_key': 'True'})
        },
        u'wallposts.mediawallpostphoto': {
            'Meta': {'object_name': 'MediaWallpostPhoto'},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'blank': 'True',
                        'related_name': "'mediawallpostphoto_wallpost_photo'",
                        'null': 'True',
                        'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL)}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL),
                        'null': 'True', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [],
                           {'default': 'None', 'max_length': '15',
                            'null': 'True', 'blank': 'True'}),
            'mediawallpost': ('django.db.models.fields.related.ForeignKey', [],
                              {'blank': 'True', 'related_name': "'photos'",
                               'null': 'True',
                               'to': u"orm['wallposts.MediaWallpost']"}),
            'photo': ('django.db.models.fields.files.ImageField', [],
                      {'max_length': '100'})
        },
        u'wallposts.reaction': {
            'Meta': {'ordering': "('created',)", 'object_name': 'Reaction'},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'related_name': "'wallpost_reactions'",
                        'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL)}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [],
                       {'blank': 'True', 'related_name': "'+'", 'null': 'True',
                        'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL)}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [],
                           {'default': 'None', 'max_length': '15',
                            'null': 'True', 'blank': 'True'}),
            'text': (
            'django.db.models.fields.TextField', [], {'max_length': '300'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'wallpost': ('django.db.models.fields.related.ForeignKey', [],
                         {'related_name': "'reactions'",
                          'to': u"orm['wallposts.Wallpost']"})
        },
        u'wallposts.systemwallpost': {
            'Meta': {'ordering': "('created',)",
                     'object_name': 'SystemWallpost',
                     '_ormbases': [u'wallposts.Wallpost']},
            'related_id': (
            'django.db.models.fields.PositiveIntegerField', [], {}),
            'related_type': ('django.db.models.fields.related.ForeignKey', [],
                             {'to': u"orm['contenttypes.ContentType']"}),
            'text': ('django.db.models.fields.TextField', [],
                     {'max_length': '300', 'blank': 'True'}),
            u'wallpost_ptr': (
            'django.db.models.fields.related.OneToOneField', [],
            {'to': u"orm['wallposts.Wallpost']", 'unique': 'True',
             'primary_key': 'True'})
        },
        u'wallposts.textwallpost': {
            'Meta': {'ordering': "('created',)", 'object_name': 'TextWallpost',
                     '_ormbases': [u'wallposts.Wallpost']},
            'text': (
            'django.db.models.fields.TextField', [], {'max_length': '300'}),
            u'wallpost_ptr': (
            'django.db.models.fields.related.OneToOneField', [],
            {'to': u"orm['wallposts.Wallpost']", 'unique': 'True',
             'primary_key': 'True'})
        },
        u'wallposts.wallpost': {
            'Meta': {'ordering': "('created',)", 'object_name': 'Wallpost'},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'blank': 'True', 'related_name': "'wallpost_wallpost'",
                        'null': 'True',
                        'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL)}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [],
                             {'related_name': "'content_type_set_for_wallpost'",
                              'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['{0}']".format(settings.AUTH_USER_MODEL),
                        'null': 'True', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [],
                           {'default': 'None', 'max_length': '15',
                            'null': 'True', 'blank': 'True'}),
            'object_id': (
            'django.db.models.fields.PositiveIntegerField', [], {}),
            'polymorphic_ctype': (
            'django.db.models.fields.related.ForeignKey', [],
            {'related_name': "u'polymorphic_wallposts.wallpost_set'",
             'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        }
    }

    complete_apps = ['wallposts']
