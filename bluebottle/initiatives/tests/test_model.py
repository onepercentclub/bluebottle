from django.test import TestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory


class InitiativeTestCase(TestCase):

    def test_properties(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        expected = '/initiatives/details/{}/dharma-initiative/'.format(initiative.id)
        self.assertEqual(initiative.full_url, expected)
