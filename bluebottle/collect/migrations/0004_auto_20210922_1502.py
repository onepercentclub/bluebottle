# Generated by Django 2.2.24 on 2021-09-22 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('collect', '0003_auto_20210920_0922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectactivity',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='collect.CollectType'),
        ),
    ]
