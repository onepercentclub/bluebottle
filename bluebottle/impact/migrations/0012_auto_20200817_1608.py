# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-08-17 14:08


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0011_auto_20200812_1038'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='impacttypetranslation',
            name='text_passed_with_value',
        ),
        migrations.AlterField(
            model_name='impactgoal',
            name='realized',
            field=models.FloatField(blank=True, help_text='Enter your impact results here when the activity is finished', null=True, verbose_name='realized'),
        ),
        migrations.AlterField(
            model_name='impactgoal',
            name='target',
            field=models.FloatField(help_text='Set a target for the impact you expect to make', null=True, verbose_name='target'),
        ),
        migrations.AlterField(
            model_name='impacttype',
            name='slug',
            field=models.SlugField(help_text='Do not change this field', max_length=100, unique=True, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='impacttypetranslation',
            name='text',
            field=models.CharField(help_text='E.g. "Save plastic" or "Reduce CO\u2082 emission"', max_length=100, verbose_name='Formulate the goal "Our goal is to..."'),
        ),
        migrations.AlterField(
            model_name='impacttypetranslation',
            name='text_passed',
            field=models.CharField(help_text='E.g. "Plastic saved" or "CO\u2082 emissions reduced"', max_length=100, verbose_name='Formulate the result in past tense'),
        ),
        migrations.AlterField(
            model_name='impacttypetranslation',
            name='text_with_target',
            field=models.CharField(help_text='E.g. \u201cSave {} kg plastic\u201d or \u201cReduce CO\u2082 emissions by {} liters\u201d.Make sure to add \u201c{}\u201d where the value should go.', max_length=100, verbose_name='Formulate the goal including the target \u201cOur goal is to\u2026\u201d'),
        ),
        migrations.AlterField(
            model_name='impacttypetranslation',
            name='unit',
            field=models.CharField(blank=True, help_text='"l" or "kg". Leave this field blank if a unit is not applicable.', max_length=100, null=True, verbose_name='unit'),
        ),
    ]
