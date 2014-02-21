# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from ..models import (Region, SubRegion, Country)
from south.exceptions import SouthError

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Region.numeric_code'
        db.alter_column(u'geo_region', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True, null=True))

        # Changing field 'Country.numeric_code'
        db.alter_column(u'geo_country', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True, null=True))

        # Changing field 'SubRegion.numeric_code'
        db.alter_column(u'geo_subregion', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True, null=True))

    def backwards(self, orm):

        # Changing field 'Region.numeric_code'
        db.alter_column(u'geo_region', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True))

        # Changing field 'Country.numeric_code'
        db.alter_column(u'geo_country', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True))

        # Changing field 'SubRegion.numeric_code'
        db.alter_column(u'geo_subregion', 'numeric_code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True))

    models = {
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
        }
    }

    complete_apps = ['geo']
