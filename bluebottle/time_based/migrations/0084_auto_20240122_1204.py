# Generated by Django 3.2.20 on 2024-01-22 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0083_merge_20231218_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dateactivity',
            name='old_online_meeting_url',
            field=models.TextField(blank=True, db_column='online_meeting_url', default='', null=True, verbose_name='online meeting link'),
        ),
        migrations.AlterField(
            model_name='dateactivity',
            name='slot_selection',
            field=models.CharField(blank=True, choices=[('all', 'All'), ('free', 'Free')], default='free', help_text='All: Participant will join all time slots. Free: Participant can pick any number of slots to join.', max_length=20, null=True, verbose_name='Slot selection'),
        ),
        migrations.AlterField(
            model_name='timebasedactivity',
            name='review_description',
            field=models.TextField(blank=True, help_text='Description of the registration step', null=True, verbose_name='Registration description'),
        ),
        migrations.AlterField(
            model_name='timebasedactivity',
            name='review_document_enabled',
            field=models.BooleanField(default=False, help_text='Can participants upload a document in the registration step', null=True, verbose_name='Registration document enabled'),
        ),
        migrations.AlterField(
            model_name='timebasedactivity',
            name='review_title',
            field=models.CharField(blank=True, help_text='Title of the registration step', max_length=255, null=True, verbose_name='Registration step title'),
        ),
    ]