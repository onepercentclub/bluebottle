from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.activities.models import Activity
from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.organizations.models import Organization
from bluebottle.files.models import Image


def run():
    for client in Client.objects.filter(schema_name__in=['onepercent', 'goodup_demo', 'voor_je_buurt']):
        with LocalTenant(client):
            for model in ActivityPubModel.objects.all():
                if model.is_local and hasattr(model, 'adopted') and model.adopted:
                    model.origin = model.adopted
                    model.adopted = None
                    model.save()

            for organization in Organization.objects.filter(origin_old__isnull=False):
                origin = organization.origin_old
                origin.adopted = organization
                origin.save()

            for image in Image.objects.filter(old_origin__isnull=False):
                origin = image.old_origin
                origin.adopted = image
                origin.save()

            for activity in Activity.objects.filter(old_origin__isnull=False):
                origin = activity.old_origin
                origin.adopted = activity
                origin.save()
