# Generated by Django 2.2.24 on 2022-06-22 07:30

from django.db import migrations, models
import django.db.models.deletion
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0030_merge_20211026_1137'),
        ('time_based', '0068_merge_20220608_1149'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timebasedactivity',
            options={'base_manager_name': 'objects'},
        ),
        migrations.AddField(
            model_name='periodactivityslot',
            name='is_online',
            field=models.NullBooleanField(choices=[(None, 'Not set yet'), (True, 'Yes, anywhere/online'), (False, 'No, enter a location')], default=None, verbose_name='is online'),
        ),
        migrations.AddField(
            model_name='periodactivityslot',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.Geolocation', verbose_name='location'),
        ),
        migrations.AddField(
            model_name='periodactivityslot',
            name='location_hint',
            field=models.TextField(blank=True, null=True, verbose_name='location hint'),
        ),
        migrations.AddField(
            model_name='periodactivityslot',
            name='online_meeting_url',
            field=models.TextField(blank=True, default='', verbose_name='online meeting link'),
        ),
        migrations.AlterField(
            model_name='skilltranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='time_based.Skill'),
        ),
    ]
