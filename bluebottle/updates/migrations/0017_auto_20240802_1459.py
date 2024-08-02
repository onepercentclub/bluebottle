# Generated by Django 3.2.20 on 2024-08-02 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0075_auto_20240723_1030'),
        ('updates', '0016_merge_0015_merge_20240707_1006_0015_team_wallposts'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='update',
            options={'ordering': ('created',), 'verbose_name': 'Update'},
        ),
        migrations.AddField(
            model_name='update',
            name='contribution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='activities.contributor', verbose_name='Related contribution'),
        ),
        migrations.AlterField(
            model_name='update',
            name='message',
            field=models.TextField(blank=True, null=True, verbose_name='message'),
        ),
    ]
