# Generated by Django 3.2.20 on 2024-09-06 13:07

from django.db import migrations, models
import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("funding_stripe", "0012_auto_20240826_1418"),
    ]

    operations = [
        migrations.AddField(
            model_name="stripepayoutaccount",
            name="requirements",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=60), default=[], size=None
            ),
            preserve_default=False,
        ),
    ]