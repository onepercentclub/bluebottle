from django.db import migrations
from django.db.models import F


def convert_partner_organization(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')

    pairs = (
        Member.objects
        .filter(partner_organization__isnull=False)
        .exclude(partner_organization__owner_id=F('id'))
        .values_list('id', 'partner_organization_id')
    )

    OrganizationMember.objects.bulk_create(
        [
            OrganizationMember(member_id=member_id, organization_id=organization_id)
            for member_id, organization_id in pairs
        ],
        ignore_conflicts=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0029_organizationmember'),
        ('members', '0108_member_office_manager'),
    ]

    operations = [
        migrations.RunPython(
            convert_partner_organization,
            migrations.RunPython.noop
        ),
    ]
