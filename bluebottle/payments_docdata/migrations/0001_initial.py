# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DocdataPayment'
        db.create_table(u'payments_docdata_docdatapayment', (
            (u'payment_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['payments.Payment'], unique=True, primary_key=True)),
            ('merchant_order_id', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('payment_cluster_id', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=200)),
            ('payment_cluster_key', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=200)),
            ('status', self.gf('django.db.models.fields.CharField')(default='new', max_length=50)),
            ('language', self.gf('django.db.models.fields.CharField')(default='en', max_length=5, blank=True)),
            ('ideal_issuer_id', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('default_pm', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('total_gross_amount', self.gf('django.db.models.fields.DecimalField')(max_digits=15, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('total_registered', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_shopper_pending', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_acquirer_pending', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_acquirer_approved', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_captured', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_refunded', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('total_charged_back', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
        ))
        db.send_create_signal(u'payments_docdata', ['DocdataPayment'])

        # Adding model 'DocdataTransaction'
        db.create_table(u'payments_docdata_docdatatransaction', (
            (u'transaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['payments.Transaction'], unique=True, primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='NEW', max_length=30)),
            ('payment_id', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True)),
            ('payment_method', self.gf('django.db.models.fields.CharField')(default='', max_length=60, blank=True)),
        ))
        db.send_create_signal(u'payments_docdata', ['DocdataTransaction'])

        # Adding model 'DocDataDirectDebitTransaction'
        db.create_table(u'payments_docdata_docdatadirectdebittransaction', (
            (u'transaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['payments.Transaction'], unique=True, primary_key=True)),
            ('account_name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('account_city', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('iban', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('bic', self.gf('django.db.models.fields.CharField')(max_length=35)),
        ))
        db.send_create_signal(u'payments_docdata', ['DocDataDirectDebitTransaction'])


    def backwards(self, orm):
        # Deleting model 'DocdataPayment'
        db.delete_table(u'payments_docdata_docdatapayment')

        # Deleting model 'DocdataTransaction'
        db.delete_table(u'payments_docdata_docdatatransaction')

        # Deleting model 'DocDataDirectDebitTransaction'
        db.delete_table(u'payments_docdata_docdatadirectdebittransaction')


    models = {
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
        u'bb_accounts.timeavailable': {
            'Meta': {'ordering': "['type']", 'object_name': 'TimeAvailable'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'bb_projects.projecttheme': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProjectTheme'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
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
            'numeric_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'oda_recipient': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.SubRegion']"})
        },
        u'geo.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'geo.subregion': {
            'Meta': {'ordering': "['name']", 'object_name': 'SubRegion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Region']"})
        },
        u'members.bookinguser': {
            'Meta': {'object_name': 'BookingUser'},
            'about': ('django.db.models.fields.TextField', [], {'max_length': '265', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'disable_token': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254', 'db_index': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'favourite_countries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'favourite_themes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['bb_projects.ProjectTheme']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'my_destinations': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'my_destination_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['offices.Office']"}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'office': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['offices.Office']", 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'primary_language': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'share_money': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'share_time_knowledge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skills': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['tasks.Skill']", 'null': 'True', 'blank': 'True'}),
            'skypename': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'time_available': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bb_accounts.TimeAvailable']", 'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'user_type': ('django.db.models.fields.CharField', [], {'default': "'person'", 'max_length': '25'}),
            'username': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'why': ('django.db.models.fields.TextField', [], {'max_length': '265', 'blank': 'True'})
        },
        u'offices.office': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Office'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Active'", 'max_length': "'30'"})
        },
        u'orders.order': {
            'Meta': {'object_name': 'Order'},
            'closed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20', 'db_index': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['members.BookingUser']", 'null': 'True', 'blank': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        u'payments.orderpayment': {
            'Meta': {'object_name': 'OrderPayment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'authorization_action': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.OrderPaymentAction']", 'unique': 'True', 'null': 'True'}),
            'closed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'integration_data': ('django.db.models.fields.TextField', [], {'default': "'{}'", 'max_length': '5000', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'to': u"orm['orders.Order']"}),
            'payment_method': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['members.BookingUser']", 'null': 'True', 'blank': 'True'})
        },
        u'payments.orderpaymentaction': {
            'Meta': {'object_name': 'OrderPaymentAction'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'payload': ('django.db.models.fields.CharField', [], {'max_length': '5000', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'})
        },
        u'payments.payment': {
            'Meta': {'ordering': "('-created', '-updated')", 'object_name': 'Payment'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_payment': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.OrderPayment']", 'unique': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_payments.payment_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payments.transaction': {
            'Meta': {'ordering': "('-created', '-updated')", 'object_name': 'Transaction'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Payment']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_payments.transaction_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payments_docdata.docdatadirectdebittransaction': {
            'Meta': {'ordering': "('-created', '-updated')", 'object_name': 'DocDataDirectDebitTransaction', '_ormbases': [u'payments.Transaction']},
            'account_city': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'bic': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'iban': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.Transaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'payments_docdata.docdatapayment': {
            'Meta': {'ordering': "('-created', '-updated')", 'object_name': 'DocdataPayment', '_ormbases': [u'payments.Payment']},
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'default_pm': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'ideal_issuer_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5', 'blank': 'True'}),
            'merchant_order_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'payment_cluster_id': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200'}),
            'payment_cluster_key': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200'}),
            u'payment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.Payment']", 'unique': 'True', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '50'}),
            'total_acquirer_approved': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_acquirer_pending': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_captured': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_charged_back': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_gross_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '15', 'decimal_places': '2'}),
            'total_refunded': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_registered': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'total_shopper_pending': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'})
        },
        u'payments_docdata.docdatatransaction': {
            'Meta': {'ordering': "('-created', '-updated')", 'object_name': 'DocdataTransaction', '_ormbases': [u'payments.Transaction']},
            'payment_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'payment_method': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '60', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'NEW'", 'max_length': '30'}),
            u'transaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.Transaction']", 'unique': 'True', 'primary_key': 'True'})
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
        },
        u'tasks.skill': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Skill'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['payments_docdata']