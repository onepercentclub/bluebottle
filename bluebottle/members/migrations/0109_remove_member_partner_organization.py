from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0108_member_office_manager'),
        ('organizations', '0030_convert_partner_organization_to_members'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='partner_organization',
        ),
    ]
