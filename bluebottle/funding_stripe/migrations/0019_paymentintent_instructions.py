# Generated by Django 3.2.20 on 2024-11-12 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funding_stripe', '0018_auto_20241112_1355'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentintent',
            name='instructions',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
