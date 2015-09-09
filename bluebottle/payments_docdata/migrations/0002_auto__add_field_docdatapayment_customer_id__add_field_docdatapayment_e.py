# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding field 'DocdataPayment.customer_id'
        db.add_column(u'payments_docdata_docdatapayment', 'customer_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(
                          default=0),
                      keep_default=False)

        # Adding field 'DocdataPayment.email'
        db.add_column(u'payments_docdata_docdatapayment', 'email',
                      self.gf('django.db.models.fields.EmailField')(default='',
                                                                    max_length=254),
                      keep_default=False)

        # Adding field 'DocdataPayment.first_name'
        db.add_column(u'payments_docdata_docdatapayment', 'first_name',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataPayment.last_name'
        db.add_column(u'payments_docdata_docdatapayment', 'last_name',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataPayment.address'
        db.add_column(u'payments_docdata_docdatapayment', 'address',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataPayment.postal_code'
        db.add_column(u'payments_docdata_docdatapayment', 'postal_code',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=20),
                      keep_default=False)

        # Adding field 'DocdataPayment.city'
        db.add_column(u'payments_docdata_docdatapayment', 'city',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'DocdataPayment.customer_id'
        db.delete_column(u'payments_docdata_docdatapayment', 'customer_id')

        # Deleting field 'DocdataPayment.email'
        db.delete_column(u'payments_docdata_docdatapayment', 'email')

        # Deleting field 'DocdataPayment.first_name'
        db.delete_column(u'payments_docdata_docdatapayment', 'first_name')

        # Deleting field 'DocdataPayment.last_name'
        db.delete_column(u'payments_docdata_docdatapayment', 'last_name')

        # Deleting field 'DocdataPayment.address'
        db.delete_column(u'payments_docdata_docdatapayment', 'address')

        # Deleting field 'DocdataPayment.postal_code'
        db.delete_column(u'payments_docdata_docdatapayment', 'postal_code')

        # Deleting field 'DocdataPayment.city'
        db.delete_column(u'payments_docdata_docdatapayment', 'city')

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'model': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'orders.order': {
            'Meta': {'object_name': 'Order'},
            'completed': ('django.db.models.fields.DateTimeField', [],
                          {'null': 'True', 'blank': 'True'}),
            'confirmed': ('django.db.models.fields.DateTimeField', [],
                          {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'total': ('django.db.models.fields.DecimalField', [],
                      {'default': '0', 'max_digits': '16',
                       'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': u"orm['test.TestBaseUser']", 'null': 'True',
                      'blank': 'True'})
        },
        u'payments.orderpayment': {
            'Meta': {'object_name': 'OrderPayment'},
            'amount': ('django.db.models.fields.DecimalField', [],
                       {'max_digits': '16', 'decimal_places': '2'}),
            'authorization_action': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.OrderPaymentAction']", 'unique': 'True',
                 'null': 'True'}),
            'closed': ('django.db.models.fields.DateTimeField', [],
                       {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'integration_data': ('django.db.models.fields.TextField', [],
                                 {'default': "'{}'", 'max_length': '5000',
                                  'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [],
                      {'related_name': "'order_payments'",
                       'to': u"orm['orders.Order']"}),
            'payment_method': ('django.db.models.fields.CharField', [],
                               {'default': "''", 'max_length': '20',
                                'blank': 'True'}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'transaction_fee': ('django.db.models.fields.DecimalField', [],
                                {'null': 'True', 'max_digits': '16',
                                 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': u"orm['test.TestBaseUser']", 'null': 'True',
                      'blank': 'True'})
        },
        u'payments.orderpaymentaction': {
            'Meta': {'object_name': 'OrderPaymentAction'},
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [],
                       {'max_length': '20', 'blank': 'True'}),
            'payload': ('django.db.models.fields.CharField', [],
                        {'max_length': '5000', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [],
                     {'max_length': '20', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [],
                    {'max_length': '2000', 'blank': 'True'})
        },
        u'payments.payment': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'Payment'},
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'order_payment': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.OrderPayment']", 'unique': 'True'}),
            'polymorphic_ctype': (
                'django.db.models.fields.related.ForeignKey', [],
                {'related_name': "u'polymorphic_payments.payment_set'",
                 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [],
                       {'default': "'started'", 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payments.transaction': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'Transaction'},
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.related.ForeignKey', [],
                        {'to': u"orm['payments.Payment']"}),
            'polymorphic_ctype': (
                'django.db.models.fields.related.ForeignKey', [],
                {'related_name': "u'polymorphic_payments.transaction_set'",
                 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payments_docdata.docdatapayment': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'DocdataPayment',
                     '_ormbases': [u'payments.Payment']},
            'address': ('django.db.models.fields.CharField', [],
                        {'default': "''", 'max_length': '200'}),
            'city': ('django.db.models.fields.CharField', [],
                     {'default': "''", 'max_length': '200'}),
            'country': ('django.db.models.fields.CharField', [],
                        {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'currency': (
                'django.db.models.fields.CharField', [], {'max_length': '10'}),
            'customer_id': ('django.db.models.fields.PositiveIntegerField', [],
                            {'default': '0'}),
            'default_pm': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '100'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'default': "''", 'max_length': '254'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '200'}),
            'ideal_issuer_id': ('django.db.models.fields.CharField', [],
                                {'default': "''", 'max_length': '100'}),
            'language': ('django.db.models.fields.CharField', [],
                         {'default': "'en'", 'max_length': '5',
                          'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [],
                          {'default': "''", 'max_length': '200'}),
            'merchant_order_id': ('django.db.models.fields.CharField', [],
                                  {'default': "''", 'max_length': '100'}),
            'payment_cluster_id': ('django.db.models.fields.CharField', [],
                                   {'default': "''", 'unique': 'True',
                                    'max_length': '200'}),
            'payment_cluster_key': ('django.db.models.fields.CharField', [],
                                    {'default': "''", 'unique': 'True',
                                     'max_length': '200'}),
            u'payment_ptr': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.Payment']", 'unique': 'True',
                 'primary_key': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [],
                            {'default': "''", 'max_length': '20'}),
            'total_acquirer_approved': (
                'django.db.models.fields.DecimalField', [],
                {'default': "'0.00'", 'max_digits': '15',
                 'decimal_places': '2'}),
            'total_acquirer_pending': (
                'django.db.models.fields.DecimalField', [],
                {'default': "'0.00'", 'max_digits': '15',
                 'decimal_places': '2'}),
            'total_captured': ('django.db.models.fields.DecimalField', [],
                               {'default': "'0.00'", 'max_digits': '15',
                                'decimal_places': '2'}),
            'total_charged_back': ('django.db.models.fields.DecimalField', [],
                                   {'default': "'0.00'", 'max_digits': '15',
                                    'decimal_places': '2'}),
            'total_gross_amount': ('django.db.models.fields.DecimalField', [],
                                   {'max_digits': '15', 'decimal_places': '2'}),
            'total_refunded': ('django.db.models.fields.DecimalField', [],
                               {'default': "'0.00'", 'max_digits': '15',
                                'decimal_places': '2'}),
            'total_registered': ('django.db.models.fields.DecimalField', [],
                                 {'default': "'0.00'", 'max_digits': '15',
                                  'decimal_places': '2'}),
            'total_shopper_pending': (
                'django.db.models.fields.DecimalField', [],
                {'default': "'0.00'", 'max_digits': '15',
                 'decimal_places': '2'})
        },
        u'payments_docdata.docdatatransaction': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'DocdataTransaction',
                     '_ormbases': [u'payments.Transaction']},
            'authorization_amount': (
                'django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'authorization_currency': ('django.db.models.fields.CharField', [],
                                       {'default': "''", 'max_length': '10',
                                        'blank': 'True'}),
            'authorization_status': ('django.db.models.fields.CharField', [],
                                     {'default': "''", 'max_length': '60',
                                      'blank': 'True'}),
            'capture_amount': (
                'django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'capture_currency': ('django.db.models.fields.CharField', [],
                                 {'default': "''", 'max_length': '10',
                                  'blank': 'True'}),
            'capture_status': ('django.db.models.fields.CharField', [],
                               {'default': "''", 'max_length': '60',
                                'blank': 'True'}),
            'docdata_id': ('django.db.models.fields.CharField', [],
                           {'unique': 'True', 'max_length': '100'}),
            'payment_method': ('django.db.models.fields.CharField', [],
                               {'default': "''", 'max_length': '60',
                                'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'NEW'", 'max_length': '30'}),
            u'transaction_ptr': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.Transaction']", 'unique': 'True',
                 'primary_key': 'True'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'object_id': (
                'django.db.models.fields.IntegerField', [],
                {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [],
                    {'related_name': "u'taggit_taggeditem_items'",
                     'to': u"orm['taggit.Tag']"})
        },
        u'test.testbaseuser': {
            'Meta': {'object_name': 'TestBaseUser'},
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
            'first_name': ('django.db.models.fields.CharField', [],
                           {'max_length': '100', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [],
                       {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [],
                       {'to': u"orm['auth.Group']", 'symmetrical': 'False',
                        'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'is_active': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'is_staff': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'is_superuser': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [],
                           {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [],
                          {'max_length': '100', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [],
                         {'max_length': '100', 'blank': 'True'}),
            'newsletter': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'password': (
                'django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [],
                             {'max_length': '50', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [],
                        {'max_length': '100', 'blank': 'True'}),
            'primary_language': (
                'django.db.models.fields.CharField', [], {'max_length': '5'}),
            'share_money': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'share_time_knowledge': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
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

    complete_apps = ['payments_docdata']
