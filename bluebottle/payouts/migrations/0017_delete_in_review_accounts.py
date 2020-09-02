# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-12-19 15:21


from django.db import migrations


def remove_accounts(apps, schema_editor):
    PlainPayoutAccount = apps.get_model('payouts', 'PlainPayoutAccount')
    Project = apps.get_model('projects', 'Project')

    projects = Project.objects.filter(
        status__slug__in=('plan-needs-work', 'plan-submitted', 'plan-new'),
        amount_asked_currency__in=('EUR', 'USD')
    )
    for project in projects:
        if project.payout_account:
            project.payout_account.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payouts', '0016_auto_20181215_2016'),
        ('projects', '0083_auto_20181129_1506'),
    ]

    operations = [
        migrations.RunPython(remove_accounts)
    ]
