# Generated by Django 4.2.17 on 2025-03-07 11:41

import bluebottle.files.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_quill.fields
import multiselectfield.db.fields
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0013_alter_document_owner_alter_image_owner_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initiatives', '0056_merge_0055_auto_20250122_1142_0055_auto_20250225_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiativeplatformsettings',
            name='enable_reviewing',
            field=models.BooleanField(default=True, help_text='Enable reviewing of initiatives and activities before they can be published.', verbose_name='Enable reviewing'),
        ),
        migrations.AlterField(
            model_name='activitysearchfilter',
            name='type',
            field=models.CharField(choices=[('country', 'Country'), ('date', 'Date'), ('distance', 'Distance'), ('is_online', 'Online / In-person'), ('skill', 'Skill'), ('team_activity', 'Individual / Team'), ('theme', 'Theme'), ('category', 'Category'), ('office', 'Office'), ('office_subregion', 'Office group'), ('office_region', 'Office region')], max_length=100),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='activity_manager',
            field=models.ForeignKey(blank=True, help_text='The co-initiator can create and edit activities for this initiative, but cannot edit the initiative itself.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_manager_%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='co-initiator'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='activity_managers',
            field=models.ManyToManyField(blank=True, help_text='Co-initiators can create and edit activities for this initiative, but cannot edit the initiative itself.', related_name='activity_managers_%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='co-initiators'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='image',
            field=bluebottle.files.fields.ImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.image'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='own_%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='promoter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promoter_%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='promoter'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='reviewer'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='story',
            field=django_quill.fields.QuillField(blank=True, verbose_name='story'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='activity_search_filters',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('country', 'Country'), ('date', 'Date'), ('distance', 'Distance'), ('is_online', 'Online / In-person'), ('skill', 'Skill'), ('team_activity', 'Individual / Team'), ('theme', 'Theme'), ('category', 'Category'), ('office', 'Office'), ('office_subregion', 'Office group'), ('office_region', 'Office region')], default=[], max_length=1000, verbose_name='Activity search: more filters'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='create_flow',
            field=models.CharField(choices=[('initiative', 'Start the create flow by creating an initiative'), ('activity', 'Directly create an activity')], default='initiative', max_length=100, verbose_name='Create flow'),
        ),
        migrations.AlterField(
            model_name='themetranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='initiatives.theme'),
        ),
        migrations.AlterUniqueTogether(
            name='themetranslation',
            unique_together={('language_code', 'master')},
        ),
        migrations.AlterModelTable(
            name='themetranslation',
            table='initiatives_theme_translation',
        ),
    ]
