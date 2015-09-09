# -*- coding: utf-8 -*-
# Generated with bb_schemamigration
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Migration(SchemaMigration):
    depends_on = (
        ('orders', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'Payment'
        db.create_table(u'payments_payment', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype',
             self.gf('django.db.models.fields.related.ForeignKey')(
                 related_name=u'polymorphic_payments.payment_set', null=True,
                 to=orm['contenttypes.ContentType'])),
            ('status', self.gf('django_fsm.db.fields.fsmfield.FSMField')(
                default='started', max_length=50)),
            ('order_payment',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['payments.OrderPayment'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'payments', ['Payment'])

        # Adding model 'OrderPaymentAction'
        db.create_table(u'payments_orderpaymentaction', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20,
                                                                  blank=True)),
            ('method',
             self.gf('django.db.models.fields.CharField')(max_length=20,
                                                          blank=True)),
            ('url',
             self.gf('django.db.models.fields.CharField')(max_length=2000,
                                                          blank=True)),
            ('payload',
             self.gf('django.db.models.fields.CharField')(max_length=5000,
                                                          blank=True)),
        ))
        db.send_create_signal(u'payments', ['OrderPaymentAction'])

        # Adding model 'OrderPayment'
        db.create_table(u'payments_orderpayment', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm[MODEL_MAP['user']['model']], null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='payments', to=orm[MODEL_MAP['order']['model']])),
            ('status', self.gf('django_fsm.db.fields.fsmfield.FSMField')(
                default='created', max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('closed',
             self.gf('django.db.models.fields.DateTimeField')(null=True,
                                                              blank=True)),
            ('amount',
             self.gf('django.db.models.fields.DecimalField')(max_digits=16,
                                                             decimal_places=2)),
            ('payment_method',
             self.gf('django.db.models.fields.CharField')(default='',
                                                          max_length=20,
                                                          blank=True)),
            ('integration_data',
             self.gf('django.db.models.fields.TextField')(default='{}',
                                                          max_length=5000,
                                                          blank=True)),
            ('authorization_action',
             self.gf('django.db.models.fields.related.OneToOneField')(
                 to=orm['payments.OrderPaymentAction'], unique=True,
                 null=True)),
        ))
        db.send_create_signal(u'payments', ['OrderPayment'])

        # Adding model 'Transaction'
        db.create_table(u'payments_transaction', (
            (u'id',
             self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype',
             self.gf('django.db.models.fields.related.ForeignKey')(
                 related_name=u'polymorphic_payments.transaction_set',
                 null=True, to=orm['contenttypes.ContentType'])),
            ('payment', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['payments.Payment'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(
                default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'payments', ['Transaction'])

    def backwards(self, orm):
        # Deleting model 'Payment'
        db.delete_table(u'payments_payment')

        # Deleting model 'OrderPaymentAction'
        db.delete_table(u'payments_orderpaymentaction')

        # Deleting model 'OrderPayment'
        db.delete_table(u'payments_orderpayment')

        # Deleting model 'Transaction'
        db.delete_table(u'payments_transaction')

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
        u'bb_accounts.timeavailable': {
            'Meta': {'ordering': "['type']", 'object_name': 'TimeAvailable'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'model': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        MODEL_MAP['order']['model_lower']: {
            'Meta': {'object_name': MODEL_MAP['order']['class']},
            'closed': ('django.db.models.fields.DateTimeField', [],
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
                     {'to': "orm['{0}']".format(MODEL_MAP['user']['model']),
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
                      {'related_name': "'payments'",
                       'to': "orm['{0}']".format(MODEL_MAP['order']['model'])}),
            'payment_method': ('django.db.models.fields.CharField', [],
                               {'default': "''", 'max_length': '20',
                                'blank': 'True'}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [],
                       {'default': "'created'", 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [],
                     {'to': "orm['{0}']".format(MODEL_MAP['user']['model']),
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
        MODEL_MAP['user']['model_lower']: {
            'Meta': {'object_name': MODEL_MAP['user']['class']},
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
                          {'max_length': '30', 'blank': 'True'}),
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
        }
    }

    complete_apps = ['payments']
