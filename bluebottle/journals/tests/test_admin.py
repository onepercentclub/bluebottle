# from bluebottle.test.utils import BluebottleTestCase
# from tenant_schemas.test.cases import TenantTestCase
# from tenant_schemas.test.client import TenantClient
#
# from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
# from django.core.urlresolvers import reverse
# from django.test import TestCase
# from django.contrib.auth.models import User
#
#
# class AdminCreateJournalTests(BluebottleTestCase):
#     """
#     For Donations, ProjectPayouts and Organization payouts:
#
#     create_new_.._journal tests:
#
#     create a journal in the admin, for a .. that already exists.
#     Check that there is already a Journal belonging to the ..
#
#     After a new journal is made, .. should be updated
#     according to the amount of the new journal.
#
#     Check if the journal has the user_reference that belongs to the
#     user that made it in the admin
#     """
#
#     def test_create_new_donation_journal(self):
#         """
#         Make a Journal in the admin and check if the
#         Journal is correctly saved in the database, including
#         the user reference that is taken from the request.
#         """
#         #response = self.client.get(user_profile_url)
#
#     def test_create_new_projectpayout_journal(self):
#         pass
#
#     def test_create_new_organization_payout_journal(self):
#         pass
