# -*- coding: utf-8 -*-
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        for client in orm['clients.Client'].objects.all():
            client.client_name = client.schema_name
            client.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'client_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'domain_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'schema_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63'})
        }
    }

    complete_apps = ['clients']
    symmetrical = True
