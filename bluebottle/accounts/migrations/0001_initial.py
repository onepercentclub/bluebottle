# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import models

user_model = settings.AUTH_USER_MODEL.lower()

class Migration(SchemaMigration):

    depends_on = (
        ('geo', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'BlueBottleUser'
        db.create_table(u'accounts_bluebottleuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=254, db_index=True)),
            ('username', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('deleted', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('user_type', self.gf('django.db.models.fields.CharField')(default='person', max_length=25)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('picture', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100, blank=True)),
            ('about', self.gf('django.db.models.fields.TextField')(max_length=265, blank=True)),
            ('why', self.gf('django.db.models.fields.TextField')(max_length=265, blank=True)),
            ('availability', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('facebook', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('twitter', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('primary_language', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('share_time_knowledge', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('share_money', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('newsletter', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('birthdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('available_time', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('contribution', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))

        app, model = settings.AUTH_USER_MODEL.split('.')
        db.send_create_signal(app, [model])


        # Adding M2M table for field groups on 'BlueBottleUser'
        # we cannot use user_model here, because it doesn't exist yet
        m2m_table_name = db.shorten_name(u'accounts_bluebottleuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bluebottleuser', models.ForeignKey(orm[u'accounts.bluebottleuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bluebottleuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'BlueBottleUser'
        m2m_table_name = db.shorten_name(u'accounts_bluebottleuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bluebottleuser', models.ForeignKey(orm[u'accounts.bluebottleuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bluebottleuser_id', 'permission_id'])

        # Adding model 'UserAddress'
        db.create_table(u'accounts_useraddress', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line1', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('line2', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Country'], null=True, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('address_type', self.gf('django.db.models.fields.CharField')(default='primary', max_length=10, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.BlueBottleUser'])),
        ))
        db.send_create_signal(u'accounts', ['UserAddress'])


    def backwards(self, orm):
        # Deleting model 'BlueBottleUser'
        db.delete_table(u'accounts_bluebottleuser')

        # Removing M2M table for field groups on 'BlueBottleUser'
        db.delete_table(db.shorten_name(u'accounts_bluebottleuser_groups'))

        # Removing M2M table for field user_permissions on 'BlueBottleUser'
        db.delete_table(db.shorten_name(u'accounts_bluebottleuser_user_permissions'))

        # Deleting model 'UserAddress'
        db.delete_table(u'accounts_useraddress')


    models = {
        'accounts.bluebottleuser': {
            'Meta': {'object_name': 'BlueBottleUser'},
            'about': ('django.db.models.fields.TextField', [], {'max_length': '265', 'blank': 'True'}),
            'availability': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'available_time': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'contribution': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254', 'db_index': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'primary_language': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'share_money': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'share_time_knowledge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'user_type': ('django.db.models.fields.CharField', [], {'default': "'person'", 'max_length': '25'}),
            'username': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'why': ('django.db.models.fields.TextField', [], {'max_length': '265', 'blank': 'True'})
        },
        u'accounts.useraddress': {
            'Meta': {'object_name': 'UserAddress'},
            'address_type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': '10', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.BlueBottleUser']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'geo.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country'},
            'alpha2_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'alpha3_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'oda_recipient': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.SubRegion']"})
        },
        u'geo.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'})
        },
        u'geo.subregion': {
            'Meta': {'ordering': "['name']", 'object_name': 'SubRegion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Region']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['accounts']