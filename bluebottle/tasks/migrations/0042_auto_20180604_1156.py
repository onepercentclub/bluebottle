# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-04 09:56
from __future__ import unicode_literals

from django.db import migrations, connection
from django.utils.translation import activate, _trans, ugettext as _

from tenant_extras.middleware import tenant_translation
from bluebottle.clients.utils import LocalTenant


def translate_skills(apps, schema_editor):
    Client = apps.get_model('clients', 'Client')
    Task = apps.get_model('tasks', 'Skill')

    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)

    with LocalTenant(tenant):
        for task in Task.objects.all():
            for translation in task.translations.all():
                activate(translation.language_code)
                _trans._active.value = tenant_translation(
                    translation.language_code, connection.tenant.client_name
                )
                translation.name = _(translation.name)
                translation.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0041_remove_untranslated_fields'),
    ]

    operations = [
        migrations.RunPython(translate_skills)
    ]
