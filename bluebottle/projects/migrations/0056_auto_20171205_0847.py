# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-12-05 07:47


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0055_merge_20171205_0847'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomProjectField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(blank=True, max_length=5000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomProjectFieldSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
                ('sequence', models.PositiveIntegerField(db_index=True, default=0, editable=False)),
                ('project_settings', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='extra_fields', to='projects.ProjectPlatformSettings')),
            ],
            options={
                'ordering': ['sequence'],
            },
        ),
        migrations.AlterField(
            model_name='projectsearchfilter',
            name='name',
            field=models.CharField(choices=[(b'location', 'Location'), (b'theme', 'Theme'), (b'skills', 'Skill'), (b'date', 'Date'), (b'status', 'Status'), (b'type', 'Type'), (b'category', 'Category')], max_length=100),
        ),
        migrations.AddField(
            model_name='customprojectfield',
            name='field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.CustomProjectFieldSettings'),
        ),
        migrations.AddField(
            model_name='customprojectfield',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project', verbose_name=b'extra'),
        ),
    ]
