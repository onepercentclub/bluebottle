from urllib.parse import urlparse, urlencode

import requests


class WebFingerClient:
    def _do_request(self, url):
        print(url)
        response = requests.get(url)
        print(response.status_code)
        response.raise_for_status()
        return response.json()

    def get(self, uri, type='application/activity+josn'):
        parsed = urlparse(uri)

        params = urlencode({'resource': uri})
        response = self._do_request(
            f'{parsed.scheme}://{parsed.netloc}/.well-known/webfinger?{params}'
        )

        for link in response['links']:
            if link['type'] == 'application/activity+json' and link['rel'] == 'self':
                return link['href']


client = WebFingerClient()
