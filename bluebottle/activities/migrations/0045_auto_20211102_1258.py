# Generated by Django 2.2.24 on 2021-11-02 11:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0044_activity_office_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='office_location',
            field=models.ForeignKey(blank=True, help_text="Office is set on activity level because the initiative is set to 'global' or no initiative has been specified.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.Location', verbose_name='office'),
        ),
        migrations.AlterField(
            model_name='effortcontribution',
            name='contribution_type',
            field=models.CharField(choices=[('organizer', 'Activity Organizer'), ('deed', 'Deed particpant'), ('collect', 'Collect contributor')], max_length=20, verbose_name='Contribution type'),
        ),
    ]
