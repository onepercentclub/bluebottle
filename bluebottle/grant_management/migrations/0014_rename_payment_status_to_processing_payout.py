from django.db import migrations


def rename_payment_status(apps, schema_editor):
    GrantApplication = apps.get_model('grant_management', 'GrantApplication')
    GrantApplication.objects.filter(status='payment').update(
        status='processing_payout'
    )


def revert_payment_status(apps, schema_editor):
    GrantApplication = apps.get_model('grant_management', 'GrantApplication')
    GrantApplication.objects.filter(status='processing_payout').update(
        status='payment'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('grant_management', '0013_grantwithdrawal'),
    ]

    operations = [
        migrations.RunPython(rename_payment_status, revert_payment_status),
    ]
