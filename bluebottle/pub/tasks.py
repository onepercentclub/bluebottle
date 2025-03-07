import requests
from celery import shared_task
from django.apps import apps


@shared_task
def publish_to_platform(app_label, model_name, instance_id, platform_id):
    """
    Generic task to publish any model to ActivityPub platform
    """
    try:
        Model = apps.get_model(app_label, model_name)
        instance = Model.objects.get(id=instance_id)
        Platform = apps.get_model('pub', 'Platform')
        platform = Platform.objects.get(id=platform_id)

        # Get the appropriate serializer
        serializer_class = instance.get_activitypub_serializer()

        # Prepare the ActivityPub create activity
        create_activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Create",
            "actor": platform.actor_url,
            "to": ["https://www.w3.org/ns/activitystreams#Public"],
            "object": serializer_class(instance).data
        }

        # Send to platform's inbox
        response = requests.post(
            platform.inbox_url,
            json=create_activity,
            headers={
                'Content-Type': 'application/activity+json',
                # TODO: Implement proper HTTP signatures
            }
        )
        response.raise_for_status()

        return True
    except Exception:
        # TODO: Add proper error handling/logging
        return False
