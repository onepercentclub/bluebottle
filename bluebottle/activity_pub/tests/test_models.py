from pprint import pprint
import json

from bluebottle.activity_pub.models import Person
from bluebottle.test.utils import BluebottleTestCase


class PersonTestCase(BluebottleTestCase):
    doc = """
        {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1"
            ],
            "type": "Person",
            "id": "https://social.example/alyssa/",
            "name": "Alyssa P. Hacker",
            "preferredUsername": "alyssa",
            "summary": "Lisp enthusiast hailing from MIT",
            "inbox": "https://social.example/alyssa/inbox/",
            "outbox": "https://social.example/alyssa/outbox/",
            "followers": "https://social.example/alyssa/followers/",
            "following": "https://social.example/alyssa/following/",
            "liked": "https://social.example/alyssa/liked/",
            "publicKey": {
                "id": "https://social.example/alyssa/publickey",
                "owner": "https://social.example/alyssa/",
                "publicKeyPem": "fewiofeion"
            }
        }
    """

    def setUp(self):
        super(PersonTestCase, self).setUp()

    @property
    def graph(self):
        return json.loads(self.doc)

    def test_save_graph(self):
        person = Person.save_graph(self.graph)

        pprint(person.to_jsonld())
