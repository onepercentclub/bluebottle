# Generated by Django 3.2.20 on 2024-09-23 09:43

from django.db import migrations, models
import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('funding_stripe', '0014_auto_20240913_1128'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stripepaymentprovider',
            name='bancontact',
        ),
        migrations.RemoveField(
            model_name='stripepaymentprovider',
            name='credit_card',
        ),
        migrations.RemoveField(
            model_name='stripepaymentprovider',
            name='direct_debit',
        ),
        migrations.RemoveField(
            model_name='stripepaymentprovider',
            name='ideal',
        ),
        migrations.AlterField(
            model_name='stripepayoutaccount',
            name='requirements',
            field=django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.CharField(max_length=60), default=list, size=None),
        ),
    ]
