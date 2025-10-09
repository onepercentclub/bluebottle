from urllib.parse import urlparse, urlencode

import requests


class WebFingerClient:
    def _do_request(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get(self, uri, type='application/activity+json'):
        parsed = urlparse(uri)
        print(parsed)

        params = urlencode({'resource': uri})
        response = self._do_request(
            f'{parsed.scheme}://{parsed.netloc}/.well-known/webfinger?{params}'
        )

        for link in response['links']:
            if link['type'] == 'application/activity+json' and link['rel'] == 'self':
                return link['href']


client = WebFingerClient()
