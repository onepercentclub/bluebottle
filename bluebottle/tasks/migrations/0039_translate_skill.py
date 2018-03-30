# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-30 09:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0038_merge_20171115_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='SkillTranslation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('_name', models.CharField(max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('master', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='tasks.Skill')),
            ],
            options={
                'managed': True,
                'db_table': 'tasks_skill_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'skill Translation',
            },
        ),
        migrations.AlterField(
            model_name='taskmember',
            name='status',
            field=models.CharField(choices=[(b'applied', 'Applied'), (b'accepted', 'Accepted'), (b'rejected', 'Rejected'), (b'stopped', 'Stopped'), (b'withdrew', 'Withdrew'), (b'realized', 'Realised'), (b'absent', 'Absent')], default=b'applied', max_length=20, verbose_name='status'),
        ),
        migrations.AlterUniqueTogether(
            name='skilltranslation',
            unique_together=set([('language_code', 'master'), ('language_code', '_name')]),
        ),
    ]
