# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-20 09:26


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_auto_20160720_1140'),
        ('surveys', '0010_auto_20160920_0854'),
    ]

    operations = [
        migrations.CreateModel(
            name='AggregateAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project')),
            ],
        ),
        migrations.AlterField(
            model_name='question',
            name='aggregation',
            field=models.CharField(blank=True, choices=[(b'sum', b'Sum'), (b'average', b'Average')], max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='aggregateanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.Question'),
        ),
    ]
