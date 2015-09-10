import json
from urlparse import urljoin
import requests

from django.db.models.signals import post_save
from django.dispatch import receiver

from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.wallposts.models import MediaWallpost, TextWallpost
from bluebottle.clients import properties


@receiver(post_save, sender=MediaWallpost)
@receiver(post_save, sender=TextWallpost)
def post_to_facebook(sender, instance, created, **kwargs):
    if created and instance.share_with_facebook:
        social = instance.author.social_auth.get(provider='facebook')
        authorization_header = 'Bearer {token}'.format(
            token=social.extra_data['access_token']
        )

        graph_url = 'https://graph.facebook.com/v2.4/me/feed'
        base_url = 'https://{domain}'.format(domain=properties.tenant.domain_url)

        link = urljoin(
            base_url,
            '/go/projects/{slug}'.format(slug=instance.content_object.slug)
        )

        # TODO, use the first image in the wallpost. However that is not saved at this
        # moment. (Maybe do this in a celery task???).
        image = urljoin(
            base_url,
            get_thumbnail(instance.content_object.image, "600x400").url
        )

        data = {
            'link': link,
            'name': instance.content_object.title,
            'caption': instance.content_object.pitch,
            'description': instance.text,
            'picture': image
        }

        # TODO: log failed requests
        requests.post(
            graph_url,
            data=json.dumps(data),
            headers={
                'Authorization': authorization_header,
                'Content-Type': 'application/json'
            }
        )
