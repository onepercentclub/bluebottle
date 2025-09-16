import logging
from io import BytesIO

import requests
from rest_framework.exceptions import ParseError

from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer

logger = logging.getLogger(__name__)


class JSONLDAdapter():
    def __init__(self):
        self.parser = JSONLDParser()
        self.renderer = JSONLDRenderer()

    def execute(self, method, url, data=None):
        kwargs = {'headers': {'Content-Type': 'application/ld+json'}}
        if data:
            kwargs['data'] = data
        try:
            response = getattr(requests, method)(url, **kwargs)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Check if the response has content
            if not response.content:
                logger.warning(f"Empty response from {url}")
                return None, None

            stream = BytesIO(response.content)
            content_type = response.headers.get("content-type", "application/json")
            return (stream, content_type)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None, None

    def do_request(self, method, url, data=None):
        result = self.execute(method, url, data)
        if result[0] is None:
            return None

        stream, media_type = result
        try:
            return self.parser.parse(stream, media_type)
        except ParseError as e:
            logger.error(f"JSON parse error from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse response from {url}: {e}")
            return None

    def get(self, url):
        return self.do_request("get", url)

    def post(self, url, data):
        return self.do_request('post', url, data)

    def sync(self, url, serializer, force=True):
        data = self.get(url)
        if data is None:
            raise ValueError(f"Failed to fetch data from {url}")

        serializer = serializer(data=data)
        serializer.is_valid(raise_exception=True)

        return serializer.save()

    def publish(self, activity):
        from bluebottle.activity_pub.serializers import ActivitySerializer

        if activity.url:
            raise TypeError('Only local activities can be published')

        data = self.renderer.render(
            ActivitySerializer().to_representation(activity)
        )

        for actor in activity.audience:
            try:
                result = self.post(actor.inbox.url, data=data)
                if result is None:
                    logger.warning(
                        f"Failed to publish to {actor.inbox.url} - received empty or invalid response"
                    )
                else:
                    logger.info(f"Successfully published to {actor.inbox.url}")
            except Exception as e:
                logger.error(f"Failed to publish to {actor.inbox.url}: {e}")
                # Continue with other actors even if one fails
                continue


adapter = JSONLDAdapter()
