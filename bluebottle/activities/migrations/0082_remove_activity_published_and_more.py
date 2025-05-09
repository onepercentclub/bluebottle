# Generated by Django 4.2.20 on 2025-03-21 10:28

import bluebottle.files.fields
from django.db import migrations, models
import django.db.models.deletion
import django_quill.fields


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0013_auto_20230706_1539'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('initiatives', '0059_merge_20250320_1136'),
        ('files', '0013_alter_document_owner_alter_image_owner_and_more'),
        ('activities', '0081_auto_20250321_1121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='published',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='transition_date',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='transition_date',
        ),
        migrations.AddField(
            model_name='activity',
            name='categories',
            field=models.ManyToManyField(blank=True, to='categories.category'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='description',
            field=django_quill.fields.QuillField(blank=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='image',
            field=bluebottle.files.fields.ImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.image'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='initiative',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='initiatives.initiative'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='video_url',
            field=models.URLField(blank=True, default='', help_text='Make your activity come alive with a video. You can paste the link to YouTube or Vimeo here.', max_length=100, null=True, verbose_name='video'),
        ),
        migrations.AlterField(
            model_name='contribution',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='contributor',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='effortcontribution',
            name='contribution_type',
            field=models.CharField(choices=[('organizer', 'Activity Organizer'), ('deed', 'Deed participant')], max_length=20, verbose_name='Contribution type'),
        ),
    ]
