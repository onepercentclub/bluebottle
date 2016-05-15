# -*- coding: utf-8 -*-
from decimal import Decimal
from south.v2 import DataMigration


class Migration(DataMigration):
    def forwards(self, orm):
        for fundraiser in orm['fundraisers.Fundraiser'].objects.all():
            fundraiser.amount = Decimal(fundraiser.amount) / 100
            fundraiser.save()

    def backwards(self, orm):
        for fundraiser in orm['fundraisers.Fundraiser'].objects.all():
            fundraiser.amount = int(fundraiser.amount * 100)
            fundraiser.save()

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
        u'bb_projects.projectphase': {
            'Meta': {'ordering': "['sequence']", 'object_name': 'ProjectPhase'},
            'active': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [],
                            {'max_length': '400', 'blank': 'True'}),
            'editable': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'owner_editable': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sequence': (
            'django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '200'}),
            'viewable': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'})
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
        u'fundraisers.fundraiser': {
            'Meta': {'object_name': 'Fundraiser'},
            'amount': ('django.db.models.fields.DecimalField', [],
                       {'max_digits': '10', 'decimal_places': '2'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [],
                         {'default': "'EUR'", 'max_length': "'10'"}),
            'deadline': (
            'django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'description': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [],
                      {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [],
                      {'to': "orm['memberds.Member']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {
            'to': "orm['projects.Project']"}),
            'title': (
            'django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.URLField', [],
                          {'default': "''", 'max_length': '100',
                           'blank': 'True'})
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
            'first_name': ('django.db.models.fields.CharField', [],
                           {'max_length': '100', 'blank': 'True'}),
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
        u'organzation.orgranization': {
            'Meta': {'ordering': "['name']",
                     'object_name': 'Organzation'},
            'account_bank_address': ('django.db.models.fields.CharField', [],
                                     {'max_length': '255', 'blank': 'True'}),
            'account_bank_city': ('django.db.models.fields.CharField', [],
                                  {'max_length': '255', 'blank': 'True'}),
            'account_bank_country': (
            'django.db.models.fields.related.ForeignKey', [],
            {'blank': 'True', 'related_name': "'account_bank_country'",
             'null': 'True', 'to': u"orm['geo.Country']"}),
            'account_bank_name': ('django.db.models.fields.CharField', [],
                                  {'max_length': '255', 'blank': 'True'}),
            'account_bank_postal_code': (
            'django.db.models.fields.CharField', [],
            {'max_length': '20', 'blank': 'True'}),
            'account_bic': ('localflavor.generic.models.BICField', [],
                            {'max_length': '11', 'blank': 'True'}),
            'account_holder_address': ('django.db.models.fields.CharField', [],
                                       {'max_length': '255', 'blank': 'True'}),
            'account_holder_city': ('django.db.models.fields.CharField', [],
                                    {'max_length': '255', 'blank': 'True'}),
            'account_holder_country': (
            'django.db.models.fields.related.ForeignKey', [],
            {'blank': 'True', 'related_name': "'account_holder_country'",
             'null': 'True', 'to': u"orm['geo.Country']"}),
            'account_holder_name': ('django.db.models.fields.CharField', [],
                                    {'max_length': '255', 'blank': 'True'}),
            'account_holder_postal_code': (
            'django.db.models.fields.CharField', [],
            {'max_length': '20', 'blank': 'True'}),
            'account_iban': ('localflavor.generic.models.IBANField', [],
                             {'max_length': '34', 'blank': 'True'}),
            'account_number': ('django.db.models.fields.CharField', [],
                               {'max_length': '255', 'blank': 'True'}),
            'account_other': ('django.db.models.fields.CharField', [],
                              {'max_length': '255', 'blank': 'True'}),
            'address_line1': ('django.db.models.fields.CharField', [],
                              {'max_length': '100', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [],
                              {'max_length': '100', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [],
                     {'max_length': '100', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [],
                        {'blank': 'True', 'related_name': "'country'",
                         'null': 'True', 'to': u"orm['geo.Country']"}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [],
                        {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [],
                      {'max_length': '75', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [],
                         {'max_length': '255', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': (
            'django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_organizations': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [],
                             {'max_length': '40', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [],
                            {'max_length': '20', 'blank': 'True'}),
            'registration': ('django.db.models.fields.files.FileField', [],
                             {'max_length': '100', 'null': 'True',
                              'blank': 'True'}),
            'skype': ('django.db.models.fields.CharField', [],
                      {'max_length': '255', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'state': ('django.db.models.fields.CharField', [],
                      {'max_length': '100', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [],
                        {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [],
                        {'max_length': '200', 'blank': 'True'})
        },
        u'projects.partnerorganization': {
            'Meta': {'object_name': 'PartnerOrganization'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [],
                      {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'})
        },
        u'projects.project': {
            'Meta': {'ordering': "['title']",
                     'object_name': 'Project'},
            'allow_overfunding': (
            'django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'amount_asked': ('bluebottle.bb_projects.fields.MoneyField', [],
                             {'default': '0', 'null': 'True',
                              'max_digits': '12', 'decimal_places': '2',
                              'blank': 'True'}),
            'amount_donated': ('bluebottle.bb_projects.fields.MoneyField', [],
                               {'default': '0', 'max_digits': '12',
                                'decimal_places': '2'}),
            'amount_needed': ('bluebottle.bb_projects.fields.MoneyField', [],
                              {'default': '0', 'max_digits': '12',
                               'decimal_places': '2'}),
            'campaign_ended': ('django.db.models.fields.DateTimeField', [],
                               {'null': 'True', 'blank': 'True'}),
            'campaign_funded': ('django.db.models.fields.DateTimeField', [],
                                {'null': 'True', 'blank': 'True'}),
            'campaign_started': ('django.db.models.fields.DateTimeField', [],
                                 {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [],
                        {'to': u"orm['geo.Country']", 'null': 'True',
                         'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [],
                               {'null': 'True', 'blank': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [],
                         {'null': 'True', 'blank': 'True'}),
            'description': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            'effects': ('django.db.models.fields.TextField', [],
                        {'null': 'True', 'blank': 'True'}),
            'favorite': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'for_who': ('django.db.models.fields.TextField', [],
                        {'null': 'True', 'blank': 'True'}),
            'future': ('django.db.models.fields.TextField', [],
                       {'null': 'True', 'blank': 'True'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [],
                      {'max_length': '255', 'blank': 'True'}),
            'is_campaign': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.related.ForeignKey', [],
                         {'to': u"orm['utils.Language']", 'null': 'True',
                          'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [],
                         {'null': 'True', 'max_digits': '21',
                          'decimal_places': '18', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [],
                          {'null': 'True', 'max_digits': '21',
                           'decimal_places': '18', 'blank': 'True'}),
            'mchanga_account': ('django.db.models.fields.CharField', [],
                                {'max_length': '100', 'null': 'True',
                                 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [],
                             {'blank': 'True', 'related_name': "'organization'",
                              'null': 'True', 'to': "orm['organizations.Oranization']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [],
                      {'related_name': "'owner'",
                       'to': "orm['members.Member']"}),
            'partner_organization': (
            'django.db.models.fields.related.ForeignKey', [],
            {'to': u"orm['projects.PartnerOrganization']", 'null': 'True',
             'blank': 'True'}),
            'pitch': (
            'django.db.models.fields.TextField', [], {'blank': 'True'}),
            'popularity': (
            'django.db.models.fields.FloatField', [], {'default': '0'}),
            'reach': ('django.db.models.fields.PositiveIntegerField', [],
                      {'null': 'True', 'blank': 'True'}),
            'skip_monthly': (
            'django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'status': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['bb_projects.ProjectPhase']"}),
            'story': ('django.db.models.fields.TextField', [],
                      {'null': 'True', 'blank': 'True'}),
            'theme': ('django.db.models.fields.related.ForeignKey', [],
                      {'to': u"orm['bb_projects.ProjectTheme']", 'null': 'True',
                       'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [],
                      {'unique': 'True', 'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.URLField', [],
                          {'default': "''", 'max_length': '100', 'null': 'True',
                           'blank': 'True'})
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
        u'utils.language': {
            'Meta': {'ordering': "['language_name']",
                     'object_name': 'Language'},
            'code': (
            'django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': (
            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'native_name': (
            'django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['fundraisers']

    symmetrical = True
