import logging
from io import BytesIO
from urllib.parse import urlparse
import requests

from django.core.files import File
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from bluebottle.activity_pub.models import Activity, Organization

logger = logging.getLogger(__name__)


@receiver([post_save])
def publish_activity(sender, instance, **kwargs):
    try:
        if isinstance(instance, Activity) and kwargs['created'] and instance.is_local:
            from bluebottle.activity_pub.adapters import JSONLDAdapter
            adapter = JSONLDAdapter()
            adapter.publish(instance)
    except Exception as e:
        print(f"Failed to publish activity: {str(e)}")
        logger.error(f"Failed to publish activity: {str(e)}")
        # Don't re-raise the exception to prevent cascade failures
        # The error is already logged for debugging purposes


@receiver([post_save])
def create_organization(sender, instance, created, **kwargs):
    if isinstance(instance, Organization) and created and not instance.organization:
        from bluebottle.organizations.models import Organization as BluebottleOrganization

        logo = None
        if instance.image:
            try:
                response = requests.get(instance.image, timeout=30)
                response.raise_for_status()
                
                parsed_url = urlparse(instance.image)
                filename = parsed_url.path.split('/')[-1] or 'organization_logo'
                image_file = File(BytesIO(response.content), name=filename)
                logo = image_file
            except Exception as e:
                logger.warning(f"Failed to download image from {instance.image}: {str(e)}")

        organization = BluebottleOrganization.objects.create(
            name=instance.name,
            description=instance.summary,
            website=instance.url,
            logo=logo,
        )
        Organization.objects.filter(pk=instance.pk).update(organization=organization)
