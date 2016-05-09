# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    depends_on = (
        ('payments', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'VoucherPayment'
        db.create_table(u'payments_voucher_voucherpayment', (
            (u'payment_ptr',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['payments.Payment'], unique=True, primary_key=True)),
            ('voucher',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 related_name='payment', unique=True,
                 to=orm['payments_voucher.Voucher'])),
        ))
        db.send_create_signal(u'payments_voucher', ['VoucherPayment'])

        # Adding model 'Voucher'
        db.create_table(u'payments_voucher_voucher', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('amount',
             self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('currency',
             self.gf('django.db.models.fields.CharField')(default='EUR',
                                                          max_length=3)),
            ('language',
             self.gf('django.db.models.fields.CharField')(default='en',
                                                          max_length=2)),
            ('message', self.gf('django.db.models.fields.TextField')(default='',
                                                                     max_length=500,
                                                                     blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(default='',
                                                                  max_length=100,
                                                                  blank=True)),
            ('status',
             self.gf('django.db.models.fields.CharField')(default='new',
                                                          max_length=20,
                                                          db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('sender',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='buyer',
                                                                   null=True,
                                                                   to=orm['members.Member'])),
            ('sender_email',
             self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('sender_name',
             self.gf('django.db.models.fields.CharField')(default='',
                                                          max_length=100,
                                                          blank=True)),
            ('receiver',
             self.gf('django.db.models.fields.related.ForeignKey')(blank=True,
                                                                   related_name='casher',
                                                                   null=True,
                                                                   to=orm['members.Member'])),
            ('receiver_email',
             self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('receiver_name',
             self.gf('django.db.models.fields.CharField')(default='',
                                                          max_length=100,
                                                          blank=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['orders.Order'], null=True)),
        ))
        db.send_create_signal(u'payments_voucher', ['Voucher'])

    def backwards(self, orm):
        # Deleting model 'VoucherPayment'
        db.delete_table(u'payments_voucher_voucherpayment')

        # Deleting model 'Voucher'
        db.delete_table(u'payments_voucher_voucher')

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
            'order_type': ('django.db.models.fields.CharField', [],
                           {'default': "'one-off'", 'max_length': "'100'"}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'total': ('django.db.models.fields.DecimalField', [],
                      {'default': '0', 'max_digits': '16',
                       'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': "orm['members.Member']",
                      'null': 'True', 'blank': 'True'})
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
                       'to': "orm['orders.Order']"}),
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
                     {'to': "orm['members.Member']",
                      'null': 'True', 'blank': 'True'})
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
        u'payments_voucher.voucher': {
            'Meta': {'object_name': 'Voucher'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'code': ('django.db.models.fields.CharField', [],
                     {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [],
                         {'default': "'EUR'", 'max_length': '3'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [],
                         {'default': "'en'", 'max_length': '2'}),
            'message': ('django.db.models.fields.TextField', [],
                        {'default': "''", 'max_length': '500',
                         'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [],
                      {'to': "orm['orders.Order']",
                       'null': 'True'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [],
                         {'blank': 'True', 'related_name': "'casher'",
                          'null': 'True', 'to':
                              "orm['members.Member']"}),
            'receiver_email': ('django.db.models.fields.EmailField',
                               [], {'max_length': '75'}),
            'receiver_name': ('django.db.models.fields.CharField', [],
                              {'default': "''", 'max_length': '100',
                               'blank': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [],
                       {'blank': 'True', 'related_name': "'buyer'",
                        'null': 'True',
                        'to': "orm['members.Member']"}),
            'sender_email': (
                'django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'sender_name': ('django.db.models.fields.CharField', [],
                            {'default': "''", 'max_length': '100',
                             'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'new'", 'max_length': '20',
                        'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payments_voucher.voucherpayment': {
            'Meta': {'ordering': "('-created', '-updated')",
                     'object_name': 'VoucherPayment',
                     '_ormbases': [u'payments.Payment']},
            u'payment_ptr': (
                'django.db.models.fields.related.OneToOneField', [],
                {'to': u"orm['payments.Payment']", 'unique': 'True',
                 'primary_key': 'True'}),
            'voucher': ('django.db.models.fields.related.OneToOneField', [],
                        {'related_name': "'payment'", 'unique': 'True',
                         'to': u"orm['payments_voucher.Voucher']"})
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

    complete_apps = ['payments_voucher']
