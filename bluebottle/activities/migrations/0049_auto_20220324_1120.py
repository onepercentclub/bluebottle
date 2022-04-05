# Generated by Django 2.2.24 on 2022-03-24 10:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0048_contributor_team'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ('-created',), 'permissions': (('api_read_team', 'Can view team through the API'), ('api_change_team', 'Can change team through the API'), ('api_change_own_team', 'Can change own team through the API')), 'verbose_name': 'Team'},
        ),
        migrations.AlterField(
            model_name='contributor',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='activities.Team'),
        ),
    ]