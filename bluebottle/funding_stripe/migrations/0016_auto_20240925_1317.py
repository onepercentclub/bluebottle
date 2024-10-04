# Generated by Django 3.2.20 on 2024-09-25 11:17

from django.db import migrations, models
import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("funding_stripe", "0015_auto_20240924_1111"),
    ]

    operations = [
        migrations.AddField(
            model_name="stripepayoutaccount",
            name="tos_accepted",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="stripepayoutaccount",
            name="requirements",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=60), default=list, size=None
            ),
        ),
    ]
