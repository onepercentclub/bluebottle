# Generated by Django 2.2.24 on 2021-11-08 10:39

from django.db import migrations, connection

from bluebottle.clients.utils import LocalTenant

DEFAULT_COLLECT_TYPES = [
    {
        'en': {
            'name': 'Clothing',
            'unit': 'Bag of clothing',
            'unit_plural': 'Bags of clothing'
        },
        'nl': {
            'name': 'Kleding',
            'unit': 'Zak kleding',
            'unit_plural': 'Zakken kleding'
        },
    }, {
        'en': {
            'name': 'Laptops',
            'unit': 'Laptop',
            'unit_plural': 'Laptops'
        },
        'nl': {
            'name': 'Laptops',
            'unit': 'Laptop',
            'unit_plural': 'Laptops'
        },
    }, {
        'en': {
            'name': 'Groceries',
            'unit': 'Crate of groceries',
            'unit_plural': 'Crates of groceries'
        },
        'nl': {
            'name': 'Boodschappen',
            'unit': 'Krat boodschappen',
            'unit_plural': 'Kratten boodschappen'
        },
    },
]


def create_defaults(apps, schema_editor):
    Client = apps.get_model('clients', 'Client')
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        CollectType = apps.get_model('collect', 'CollectType')
        CollectTypeTranslation = apps.get_model('collect', 'CollectTypeTranslation')

        for collect_type in DEFAULT_COLLECT_TYPES:
            model = CollectType.objects.create(disabled=False)

            for lang, translation in collect_type.items():
                CollectTypeTranslation.objects.create(
                    language_code=lang,
                    master=model,
                    **translation
                )


class Migration(migrations.Migration):

    dependencies = [
        ('collect', '0013_auto_20211108_1113'),
    ]

    operations = [
        migrations.RunPython(create_defaults)
    ]