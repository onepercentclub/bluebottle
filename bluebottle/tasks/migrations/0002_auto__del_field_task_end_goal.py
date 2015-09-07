# -*- coding: utf-8 -*-
# Generated with bb_schemamigration
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Deleting field 'Task.end_goal'
        db.delete_column(MODEL_MAP['task']['table'], 'end_goal')

    def backwards(self, orm):
        # User chose to not deal with backwards NULL issues for 'Task.end_goal'
        raise RuntimeError(
            "Cannot reverse this migration. 'Task.end_goal' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct migration        # Adding field 'Task.end_goal'
        db.add_column(MODEL_MAP['task']['table'], 'end_goal',
                      self.gf('django.db.models.fields.TextField')(),
                      keep_default=False)

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
        u'bb_projects.projectphase': {
            'Meta': {'ordering': "['sequence']", 'object_name': 'ProjectPhase'},
            'active': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [],
                            {'max_length': '400', 'blank': 'True'}),
            'editable': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'owner_editable': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'}),
            'oda_recipient': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'subregion': ('django.db.models.fields.related.ForeignKey', [],
                          {'to': u"orm['geo.SubRegion']"})
        },
        u'geo.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'})
        },
        u'geo.subregion': {
            'Meta': {'ordering': "['name']", 'object_name': 'SubRegion'},
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'numeric_code': ('django.db.models.fields.CharField', [],
                             {'max_length': '3', 'unique': 'True',
                              'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [],
                       {'to': u"orm['geo.Region']"})
        },
        MODEL_MAP['user']['model_lower']: {
            'Meta': {'object_name': MODEL_MAP['user']['class']},
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
            'primary_language': (
                'django.db.models.fields.CharField', [], {'max_length': '5'}),
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
        MODEL_MAP['organization']['model_lower']: {
            'Meta': {'ordering': "['name']",
                     'object_name': MODEL_MAP['organization']['class']},
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
            'account_bic': ('django_iban.fields.SWIFTBICField', [],
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
            'account_iban': ('django_iban.fields.IBANField', [],
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
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
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [],
                      {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [],
                     {'unique': 'True', 'max_length': '100'})
        },
        MODEL_MAP['project']['model_lower']: {
            'Meta': {'ordering': "['title']",
                     'object_name': MODEL_MAP['project']['class']},
            'allow_overfunding': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'True'}),
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
                'django.db.models.fields.BooleanField', [],
                {'default': 'True'}),
            'for_who': ('django.db.models.fields.TextField', [],
                        {'null': 'True', 'blank': 'True'}),
            'future': ('django.db.models.fields.TextField', [],
                       {'null': 'True', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [],
                      {'max_length': '255', 'blank': 'True'}),
            'is_campaign': (
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
            'language': ('django.db.models.fields.related.ForeignKey', [],
                         {'to': u"orm['utils.Language']", 'null': 'True',
                          'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [],
                         {'null': 'True', 'max_digits': '21',
                          'decimal_places': '18', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [],
                          {'null': 'True', 'max_digits': '21',
                           'decimal_places': '18', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [],
                             {'blank': 'True', 'related_name': "'organization'",
                              'null': 'True', 'to': "orm['{0}']".format(
                                 MODEL_MAP['organization']['model'])}),
            'owner': ('django.db.models.fields.related.ForeignKey', [],
                      {'related_name': "'owner'",
                       'to': "orm['{0}']".format(MODEL_MAP['user']['model'])}),
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
                'django.db.models.fields.BooleanField', [],
                {'default': 'False'}),
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
        MODEL_MAP['task_skill']['model_lower']: {
            'Meta': {'ordering': "('id',)",
                     'object_name': MODEL_MAP['task_skill']['class']},
            'description': (
                'django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [],
                     {'unique': 'True', 'max_length': '100'}),
            'name_nl': ('django.db.models.fields.CharField', [],
                        {'unique': 'True', 'max_length': '100'})
        },
        MODEL_MAP['task']['model_lower']: {
            'Meta': {'ordering': "['-created']",
                     'object_name': MODEL_MAP['task']['class']},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'related_name': "u'tasks_task_related'",
                        'to': "orm['{0}']".format(MODEL_MAP['user']['model'])}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'date_status_change': ('django.db.models.fields.DateTimeField', [],
                                   {'null': 'True', 'blank': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'location': (
                'django.db.models.fields.CharField', [], {'max_length': '200'}),
            'people_needed': (
                'django.db.models.fields.PositiveIntegerField', [],
                {'default': '1'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {
                'to': "orm['{0}']".format(MODEL_MAP['project']['model'])}),
            'skill': ('django.db.models.fields.related.ForeignKey', [], {
                'to': "orm['{0}']".format(MODEL_MAP['task_skill']['model']),
                'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'open'", 'max_length': '20'}),
            'time_needed': (
                'django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        MODEL_MAP['task_file']['model_lower']: {
            'Meta': {'object_name': MODEL_MAP['task_file']['class']},
            'author': ('django.db.models.fields.related.ForeignKey', [],
                       {'related_name': "u'tasks_taskfile_related'",
                        'to': "orm['{0}']".format(MODEL_MAP['user']['model'])}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [],
                     {'max_length': '100'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [],
                     {'related_name': "'files'",
                      'to': "orm['{0}']".format(MODEL_MAP['task']['model'])}),
            'title': (
                'django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        MODEL_MAP['task_member']['model_lower']: {
            'Meta': {'object_name': MODEL_MAP['task_member']['class']},
            'comment': (
                'django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [],
                       {'related_name': "u'tasks_taskmember_related'",
                        'to': "orm['{0}']".format(MODEL_MAP['user']['model'])}),
            'motivation': (
                'django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [],
                       {'default': "'applied'", 'max_length': '20'}),
            'task': ('django.db.models.fields.related.ForeignKey', [],
                     {'related_name': "'members'",
                      'to': "orm['{0}']".format(MODEL_MAP['task']['model'])}),
            'time_spent': (
                'django.db.models.fields.PositiveSmallIntegerField', [],
                {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [],
                        {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'utils.language': {
            'Meta': {'ordering': "['language_name']",
                     'object_name': 'Language'},
            'code': (
                'django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': (
                'django.db.models.fields.AutoField', [],
                {'primary_key': 'True'}),
            'language_name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'}),
            'native_name': (
                'django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = [MODEL_MAP['task_file']['app']]
