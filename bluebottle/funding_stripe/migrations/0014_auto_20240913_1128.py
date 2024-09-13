# Generated by Django 3.2.20 on 2024-09-13 09:28

from django.db import migrations

from bluebottle.funding_stripe.models import StripePayoutAccount


def set_business_type(apps, schema_editor):
    StripePayoutAccount = apps.get_model('funding_stripe', 'StripePayoutAccount')
    StripePayoutAccount.objects.update(business_type='individual')


class Migration(migrations.Migration):

    dependencies = [
        ('funding_stripe', '0013_stripepayoutaccount_requirements'),
    ]

    operations = [
        migrations.RunPython(set_business_type, migrations.RunPython.noop),
    ]
