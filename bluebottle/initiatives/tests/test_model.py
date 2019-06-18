from django.test import TestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory


class InitiativeTestCase(TestCase):

    def test_properties(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        expected = '/initiatives/details/{}/dharma-initiative/'.format(initiative.id)
        self.assertEqual(initiative.full_url, expected)

    def test_status_changes(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        self.assertEqual(initiative.status, 'draft')

        initiative.transitions.submit()
        self.assertEqual(initiative.status, 'submitted')

        initiative.transitions.needs_work()
        self.assertEqual(initiative.status, 'needs_work')

        initiative.transitions.resubmit()
        self.assertEqual(initiative.status, 'submitted')

        initiative.transitions.approve()
        self.assertEqual(initiative.status, 'approved')

        initiative.transitions.close()
        self.assertEqual(initiative.status, 'closed')

        initiative.transitions.reopen()
        self.assertEqual(initiative.status, 'submitted')
