from bluebottle.funding_lipisha.effects import GenerateLipishaAccountsEffect
from bluebottle.funding_lipisha.tests.factories import LipishaBankAccountFactory
from bluebottle.test.utils import TriggerTestCase


class LipishaAccountTriggerTests(TriggerTestCase):

    factory = LipishaBankAccountFactory
    defaults = {}

    def test_verify(self):
        self.create()
        self.model.states.verify()

        with self.execute():
            self.assertEqual(self.model.status, 'verified')
            self.assertEffect(GenerateLipishaAccountsEffect)
