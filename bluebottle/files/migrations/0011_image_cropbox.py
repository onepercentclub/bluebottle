# Generated by Django 3.2.20 on 2025-01-10 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0010_alter_relatedimage_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='cropbox',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
