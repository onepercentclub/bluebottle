import json
import os

import pyld.documentloader.requests

requests_document_loader = pyld.documentloader.requests.requests_document_loader()

json_ld_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'json-ld'
)

local_documents = {
    'https://www.w3.org/ns/activitystreams': 'activitystreams.json',
    'https://w3id.org/security/v1': 'security.json',
    'https://goodup.com/json-ld': 'goodup.json',
}


def local_document_loader(url, options={}):
    """
    Retrieves JSON-LD at the given URL.

    :param url: the URL to retrieve.

    :return: the RemoteDocument.
    """
    filename = os.path.join(json_ld_path, local_documents.get(url, ''))

    if filename and os.path.exists(filename):
        with open(filename) as f:
            return {
                'contentType': 'application/ld+json',
                'contextUrl': None,
                'documentUrl': url,
                'document': json.load(f)
            }
    else:
        return requests_document_loader(url, options)
