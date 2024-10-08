# Generated by Django 3.2.20 on 2024-09-17 06:21

from django.db import migrations

def set_default_amounts(apps, schema_editor):
    PledgePaymentProvider = apps.get_model('funding_pledge', 'PledgePaymentProvider')
    provider = PledgePaymentProvider.objects.first()
    if provider and provider.paymentcurrency_set.count() == 0:
        print('Setting default values for pledge.')
        provider.paymentcurrency_set.create(
            code='EUR',
            default1=100,
            default2=200,
            default3=500,
            default4=1000,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('funding_pledge', '0005_auto_20191111_1331'),
    ]

    operations = [
        migrations.RunPython(
            set_default_amounts,
            migrations.RunPython.noop,
        )
    ]
