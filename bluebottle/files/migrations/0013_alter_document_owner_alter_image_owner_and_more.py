<<<<<<< HEAD
# Generated by Django 4.2.17 on 2025-03-07 11:41
=======
# Generated by Django 4.2.17 on 2025-03-05 15:18
>>>>>>> origin/ticket/multi-region-manager

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('files', '0012_auto_20250113_1704'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='own_%(class)s', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='image',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='own_%(class)s', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='privatedocument',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='own_%(class)s', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
    ]
