# Generated by Django 2.2.24 on 2022-03-24 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0050_auto_20220324_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='status',
            field=models.CharField(default='open', max_length=40),
            preserve_default=False,
        ),
    ]