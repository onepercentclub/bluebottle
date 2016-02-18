# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BankTransactionCategory'
        db.create_table(u'accounting_banktransactioncategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'accounting', ['BankTransactionCategory'])

        # Adding model 'BankTransaction'
        db.create_table(u'accounting_banktransaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.BankTransactionCategory'], null=True, blank=True)),
            ('payout', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['payouts.ProjectPayout'], null=True, blank=True)),
            ('remote_payout', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.RemoteDocdataPayout'], null=True, blank=True)),
            ('remote_payment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.RemoteDocdataPayment'], null=True, blank=True)),
            ('sender_account', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('interest_date', self.gf('django.db.models.fields.DateField')()),
            ('credit_debit', self.gf('django.db.models.fields.CharField')(max_length=1, db_index=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=14, decimal_places=2)),
            ('counter_account', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('counter_name', self.gf('django.db.models.fields.CharField')(max_length=70)),
            ('book_date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('book_code', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('filler', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('description1', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('description2', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('description3', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('description4', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('description5', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('description6', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('end_to_end_id', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('id_recipient', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('mandate_id', self.gf('django.db.models.fields.CharField')(max_length=35, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('status_remarks', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
        ))
        db.send_create_signal(u'accounting', ['BankTransaction'])

        # Adding model 'RemoteDocdataPayout'
        db.create_table(u'accounting_remotedocdatapayout', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payout_reference', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('payout_date', self.gf('django.db.models.fields.DateField')(db_index=True, null=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(db_index=True, null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(db_index=True, null=True, blank=True)),
            ('collected_amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=2, blank=True)),
            ('payout_amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=2, blank=True)),
        ))
        db.send_create_signal(u'accounting', ['RemoteDocdataPayout'])

        # Adding model 'RemoteDocdataPayment'
        db.create_table(u'accounting_remotedocdatapayment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('merchant_reference', self.gf('django.db.models.fields.CharField')(max_length=35, db_index=True)),
            ('triple_deal_reference', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('payment_type', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('amount_collected', self.gf('django.db.models.fields.DecimalField')(max_digits=14, decimal_places=2)),
            ('currency_amount_collected', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('tpcd', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=2, blank=True)),
            ('currency_tpcd', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('tpci', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=2, blank=True)),
            ('currency_tpci', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('docdata_fee', self.gf('django.db.models.fields.DecimalField')(max_digits=14, decimal_places=2)),
            ('currency_docdata_fee', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('local_payment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['payments.Payment'], null=True)),
            ('remote_payout', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.RemoteDocdataPayout'], null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('status_remarks', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
        ))
        db.send_create_signal(u'accounting', ['RemoteDocdataPayment'])


    def backwards(self, orm):
        # Deleting model 'BankTransactionCategory'
        db.delete_table(u'accounting_banktransactioncategory')

        # Deleting model 'BankTransaction'
        db.delete_table(u'accounting_banktransaction')

        # Deleting model 'RemoteDocdataPayout'
        db.delete_table(u'accounting_remotedocdatapayout')

        # Deleting model 'RemoteDocdataPayment'
        db.delete_table(u'accounting_remotedocdatapayment')


    models = {
        u'accounting.banktransaction': {
            'Meta': {'object_name': 'BankTransaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '14', 'decimal_places': '2'}),
            'book_code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'book_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.BankTransactionCategory']", 'null': 'True', 'blank': 'True'}),
            'counter_account': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'counter_name': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'credit_debit': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'description1': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'description2': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'description3': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'description4': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'description5': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'description6': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'end_to_end_id': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'filler': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_recipient': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'interest_date': ('django.db.models.fields.DateField', [], {}),
            'mandate_id': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'payout': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payouts.ProjectPayout']", 'null': 'True', 'blank': 'True'}),
            'remote_payment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.RemoteDocdataPayment']", 'null': 'True', 'blank': 'True'}),
            'remote_payout': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.RemoteDocdataPayout']", 'null': 'True', 'blank': 'True'}),
            'sender_account': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'status_remarks': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        },
        u'accounting.banktransactioncategory': {
            'Meta': {'object_name': 'BankTransactionCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'accounting.remotedocdatapayment': {
            'Meta': {'ordering': "('-remote_payout__payout_date',)", 'object_name': 'RemoteDocdataPayment'},
            'amount_collected': ('django.db.models.fields.DecimalField', [], {'max_digits': '14', 'decimal_places': '2'}),
            'currency_amount_collected': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'currency_docdata_fee': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'currency_tpcd': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'currency_tpci': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'docdata_fee': ('django.db.models.fields.DecimalField', [], {'max_digits': '14', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_payment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Payment']", 'null': 'True'}),
            'merchant_reference': ('django.db.models.fields.CharField', [], {'max_length': '35', 'db_index': 'True'}),
            'payment_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'remote_payout': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting.RemoteDocdataPayout']", 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'status_remarks': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'tpcd': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'}),
            'tpci': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'}),
            'triple_deal_reference': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'})
        },
        u'accounting.remotedocdatapayout': {
            'Meta': {'ordering': "('-payout_date',)", 'object_name': 'RemoteDocdataPayout'},
            'collected_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payout_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'}),
            'payout_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'payout_reference': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
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
        u'bb_projects.projectphase': {
            'Meta': {'ordering': "['sequence']", 'object_name': 'ProjectPhase'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'owner_editable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'viewable': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
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
        u'members.member': {
            'Meta': {'object_name': 'Member'},
            'about_me': ('django.db.models.fields.TextField', [], {'max_length': '265', 'blank': 'True'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'campaign_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'disable_token': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'primary_language': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'share_money': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'share_time_knowledge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'user_type': ('django.db.models.fields.CharField', [], {'default': "'person'", 'max_length': '25'}),
            'username': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'orders.order': {
            'Meta': {'object_name': 'Order'},
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'confirmed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_type': ('django.db.models.fields.CharField', [], {'default': "'one-off'", 'max_length': "'100'"}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [], {'default': "'created'", 'max_length': '50'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['members.Member']", 'null': 'True', 'blank': 'True'})
        },
        u'organizations.organization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Organization'},
            'account_bank_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_bank_city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_bank_country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'account_bank_country'", 'null': 'True', 'to': u"orm['geo.Country']"}),
            'account_bank_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_bank_postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'account_bic': ('localflavor.generic.models.BICField', [], {'max_length': '11', 'blank': 'True'}),
            'account_holder_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_holder_city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_holder_country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'account_holder_country'", 'null': 'True', 'to': u"orm['geo.Country']"}),
            'account_holder_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_holder_postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'account_iban': ('localflavor.generic.models.IBANField', [], {'max_length': '34', 'blank': 'True'}),
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'account_other': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'country'", 'null': 'True', 'to': u"orm['geo.Country']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_organizations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'registration': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'payments.orderpayment': {
            'Meta': {'object_name': 'OrderPayment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'authorization_action': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['payments.OrderPaymentAction']", 'unique': 'True', 'null': 'True'}),
            'closed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'integration_data': ('django.db.models.fields.TextField', [], {'default': "'{}'", 'max_length': '5000', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_payments'", 'to': u"orm['orders.Order']"}),
            'payment_method': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [], {'default': "'created'", 'max_length': '50'}),
            'transaction_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['members.Member']", 'null': 'True', 'blank': 'True'})
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
            'status': ('django_fsm.db.fields.fsmfield.FSMField', [], {'default': "'started'", 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'payouts.projectpayout': {
            'Meta': {'ordering': "['-created']", 'object_name': 'ProjectPayout'},
            'amount_payable': ('bluebottle.bb_projects.fields.MoneyField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'amount_raised': ('bluebottle.bb_projects.fields.MoneyField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'completed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description_line1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'description_line2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'description_line3': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'description_line4': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_reference': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'organization_fee': ('bluebottle.bb_projects.fields.MoneyField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'payout_rule': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'planned': ('django.db.models.fields.DateField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Project']"}),
            'receiver_account_bic': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'receiver_account_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'receiver_account_country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'receiver_account_iban': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'receiver_account_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'receiver_account_number': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sender_account_number': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'projects.partnerorganization': {
            'Meta': {'object_name': 'PartnerOrganization'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'projects.project': {
            'Meta': {'ordering': "['title']", 'object_name': 'Project'},
            'allow_overfunding': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'amount_asked': ('bluebottle.bb_projects.fields.MoneyField', [], {'default': '0', 'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'amount_donated': ('bluebottle.bb_projects.fields.MoneyField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'amount_needed': ('bluebottle.bb_projects.fields.MoneyField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'campaign_ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'campaign_funded': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'campaign_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'effects': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'favorite': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'for_who': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'future': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'is_campaign': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Language']", 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '21', 'decimal_places': '18', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '21', 'decimal_places': '18', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'organization'", 'null': 'True', 'to': u"orm['organizations.Organization']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owner'", 'to': u"orm['members.Member']"}),
            'partner_organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.PartnerOrganization']", 'null': 'True', 'blank': 'True'}),
            'pitch': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'popularity': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'reach': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'skip_monthly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bb_projects.ProjectPhase']"}),
            'story': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bb_projects.ProjectTheme']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'utils.language': {
            'Meta': {'ordering': "['language_name']", 'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'native_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['accounting']