# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding field 'DocdataDirectdebitPayment.customer_id'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment',
                      'customer_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(
                          default=0),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.email'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment', 'email',
                      self.gf('django.db.models.fields.EmailField')(default='',
                                                                    max_length=254),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.first_name'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment',
                      'first_name',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.last_name'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment',
                      'last_name',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.address'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment', 'address',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.postal_code'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment',
                      'postal_code',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=20),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.city'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment', 'city',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

        # Adding field 'DocdataDirectdebitPayment.ip_address'
        db.add_column(u'payments_docdata_docdatadirectdebitpayment',
                      'ip_address',
                      self.gf('django.db.models.fields.CharField')(default='',
                                                                   max_length=200),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'DocdataDirectdebitPayment.customer_id'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'customer_id')

        # Deleting field 'DocdataDirectdebitPayment.email'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment', 'email')

        # Deleting field 'DocdataDirectdebitPayment.first_name'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'first_name')

        # Deleting field 'DocdataDirectdebitPayment.last_name'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'last_name')

        # Deleting field 'DocdataDirectdebitPayment.address'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'address')

        # Deleting field 'DocdataDirectdebitPayment.postal_code'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'postal_code')

        # Deleting field 'DocdataDirectdebitPayment.city'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment', 'city')

        # Deleting field 'DocdataDirectdebitPayment.ip_address'
        db.delete_column(u'payments_docdata_docdatadirectdebitpayment',
                         'ip_address')

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
        u'members.member': {
            'Meta': {'object_name': 'Member'},
            'about_me': ('django.db.models.fields.TextField', [],
                         {'max_length': '265', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [],
                          {'null': 'True', 'blank': 'True'}),
            'campaign_notifications': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'True'}),
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
            'primary_language': ('django.db.models.fields.CharField', [],
                                 {'default': "'en'", 'max_length': '5'}),
            'share_money': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'share_time_knowledge': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
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
            'order_type': ('django.db.models.fields.CharField', [],
                           {'default': "'one-off'", 'max_length': "'100'"}),
            'status': ('django_fsm.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'total': ('django.db.models.fields.DecimalField', [],
                      {'default': '0', 'max_digits': '16',
                       'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': u"orm['members.Member']", 'null': 'True',
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
            'status': ('django_fsm.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'transaction_fee': ('django.db.models.fields.DecimalField', [],
                                {'null': 'True', 'max_digits': '16',
                                 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': u"orm['members.Member']", 'null': 'True',
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
            'status': ('django_fsm.FSMField', [],
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
        u'payments_docdata.docdatadirectdebitpayment': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'DocdataDirectdebitPayment'},
            'account_city': (
                'django.db.models.fields.CharField', [], {'max_length': '35'}),
            'account_name': (
                'django.db.models.fields.CharField', [], {'max_length': '35'}),
            'address': ('django.db.models.fields.CharField', [],
                        {'default': "''", 'max_length': '200'}),
            'agree': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'bic': (
                'django.db.models.fields.CharField', [], {'max_length': '35'}),
            'city': ('django.db.models.fields.CharField', [],
                     {'default': "''", 'max_length': '200'}),
            'country': ('django.db.models.fields.CharField', [],
                        {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'currency': (
                'django.db.models.fields.CharField', [], {'max_length': '10'}),
            'customer_id': ('django.db.models.fields.PositiveIntegerField', [],
                            {'default': '0'}),
            'default_pm': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'default': "''", 'max_length': '254'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '200'}),
            'iban': (
                'django.db.models.fields.CharField', [], {'max_length': '35'}),
            'ideal_issuer_id': ('django.db.models.fields.CharField', [],
                                {'default': "''", 'max_length': '100'}),
            'ip_address': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '200'}),
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
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_acquirer_pending': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_captured': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_charged_back': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_gross_amount': (
                'django.db.models.fields.IntegerField', [], {}),
            'total_refunded': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_registered': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_shopper_pending': (
                'django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'payments_docdata.docdatapayment': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'DocdataPayment'},
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
            'default_pm': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'default': "''", 'max_length': '254'}),
            'first_name': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '200'}),
            'ideal_issuer_id': ('django.db.models.fields.CharField', [],
                                {'default': "''", 'max_length': '100'}),
            'ip_address': ('django.db.models.fields.CharField', [],
                           {'default': "''", 'max_length': '200'}),
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
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_acquirer_pending': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_captured': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_charged_back': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_gross_amount': (
                'django.db.models.fields.IntegerField', [], {}),
            'total_refunded': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_registered': (
                'django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_shopper_pending': (
                'django.db.models.fields.IntegerField', [], {'default': '0'})
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
            'docdata_id': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'payment_method': ('django.db.models.fields.CharField', [],
                               {'default': "''", 'max_length': '60',
                                'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'NEW'", 'max_length': '30'}),
            u'transaction_ptr': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.Transaction']", 'unique': 'True',
                 'primary_key': 'True'})
        }
    }

    complete_apps = ['payments_docdata']
