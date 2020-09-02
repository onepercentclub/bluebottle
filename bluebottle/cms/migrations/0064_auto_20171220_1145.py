# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-12-20 10:45


from django.db import migrations

from bluebottle.cms.models import Stat as RealStat


def migrate_stats_title(apps, schema_editor):
    Stat = apps.get_model('cms', 'Stat')

    for stat in Stat.objects.filter(title=''):
        try:
            stat.title = Stat.objects.filter(
                block__language_code=stat.block.language_code,
                block__placeholder=None,
                type=stat.type
            ).exclude(title='').get().title

        except Stat.DoesNotExist:
            try:
                stat.title = Stat.objects.filter(
                    type=stat.type, block__language_code=stat.block.language_code
                ).exclude(title='')[0].title
            except IndexError:
                if stat.type != 'manual':
                    stat.title = dict(RealStat.STAT_CHOICES)[stat.type]

        stat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0063_auto_20171204_1049'),
    ]

    operations = [
        migrations.RunPython(migrate_stats_title),
    ]
