# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-11-06 09:41


from django.db import migrations


def migrate_project_blocks(apps, schema_editor):
    ProjectsContent = apps.get_model('cms', 'ProjectsContent')
    ActivitiesContent = apps.get_model('cms', 'ActivitiesContent')
    Initiative = apps.get_model('initiatives', 'Initiative')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    activity_content_ctype = ContentType.objects.get_for_model(ActivitiesContent)

    for projects_content in ProjectsContent.objects.all():
        activities_content = ActivitiesContent.objects.create(
            title=projects_content.title,
            sub_title=projects_content.sub_title,
            sort_order=projects_content.sort_order,
            placeholder=projects_content.placeholder,
            parent_id=projects_content.parent_id,
            language_code=projects_content.language_code,
            polymorphic_ctype_id=activity_content_ctype.pk,
            parent_type_id=projects_content.parent_type_id,
            highlighted=projects_content.from_homepage
        )
        for project in projects_content.projects.all():
            initiative = Initiative.objects.get(slug=project.slug)

            for activity in initiative.activities.all():
                activities_content.activities.add(activity)

        activities_content.save()
        projects_content.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0091_project_to_initiatives'),
        ('cms', '0055_migrate_statistics'),
    ]

    operations = [
        migrations.RunPython(migrate_project_blocks)
    ]
