from bluebottle.activity_pub.utils import resource_type_from_iri, type_from_iri
from bluebottle.test.utils import BluebottleTestCase


class ResourceTypeFromIriTestCase(BluebottleTestCase):
    def test_infers_organization_from_path(self):
        iri = 'http://mars.localhost:3000/api/json-ld/organization/5'
        self.assertEqual(type_from_iri(iri), 'Organization')

    def test_maps_actor_to_organization_when_allowed(self):
        iri = 'http://mars.localhost:3000/api/json-ld/actor/32'
        self.assertEqual(
            resource_type_from_iri(iri, ['Organization', 'Person']),
            'Organization'
        )

    def test_falls_back_to_first_allowed_type(self):
        iri = 'http://mars.localhost:3000/api/json-ld/unknown/1'
        self.assertEqual(
            resource_type_from_iri(iri, ['Organization', 'Person']),
            'Organization'
        )
