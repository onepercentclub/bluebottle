# Generated by Django 2.2.20 on 2021-09-14 09:34

from django.db import migrations, models
import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0005_auto_20210628_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segment',
            name='alternate_names',
            field=django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, default=list, size=None),
        ),
    ]
