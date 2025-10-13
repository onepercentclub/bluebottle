from urllib.parse import urlparse, urlencode, urlunparse

import requests


class WebFingerClient:
    def _do_request(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get(self, uri, type='application/activity+josn'):
        parsed = urlparse(uri)

        try:
            params = urlencode({'resource': uri})
            response = self._do_request(
                f'{parsed.scheme}://{parsed.netloc}/.well-known/webfinger?{params}'
            )
        except requests.exceptions.HTTPError:
            params = urlencode({
                'resource': urlunparse((parsed.scheme, parsed.netloc, '', None, None, None ))
            })
            response = self._do_request(
                f'{parsed.scheme}://{parsed.netloc}/.well-known/webfinger?{params}'
            )


        for link in response['links']:
            if link['type'] == 'application/activity+json' and link['rel'] == 'self':
                return link['href']


client = WebFingerClient()
