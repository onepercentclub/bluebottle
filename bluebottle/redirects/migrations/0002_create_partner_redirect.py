# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db import connection
from bluebottle.clients.utils import LocalTenant

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        with LocalTenant(connection.tenant):
            try:
                orm.Redirect.objects.create(old_path="/pp/(.*)",
                                            new_path="/projects?category=$1",
                                            regular_expression=True
                                            )
            except Exception as e:
                #Redirect may exist, if so, catch the exception and proceed
                pass

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'redirects.redirect': {
            'Meta': {'ordering': "('fallback_redirect', 'regular_expression', 'old_path')", 'object_name': 'Redirect', 'db_table': "'django_redirect'"},
            'fallback_redirect': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'nr_times_visited': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'old_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'regular_expression': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['redirects']
    symmetrical = True
