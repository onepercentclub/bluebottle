from bluebottle.activity_links.documents import LinkedFundingDocument
from bluebottle.activity_links.tests.factories import LinkedFundingFactory
from bluebottle.funding.documents import FundingDocument
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase

from django.test.utils import override_settings


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
class LinkedActivityDocumentIdTestCase(BluebottleTestCase):
    def test_linked_funding_document_uses_prefixed_id(self):
        linked_funding = LinkedFundingFactory.create(host_organization=OrganizationFactory.create())
        funding = FundingFactory.create()

        linked_doc_id = LinkedFundingDocument.generate_id(linked_funding)
        funding_doc_id = FundingDocument.generate_id(funding)

        self.assertEqual(linked_doc_id, f'linked_{linked_funding.pk}')
        self.assertEqual(funding_doc_id, funding.pk)
        self.assertNotEqual(linked_doc_id, str(funding_doc_id))
