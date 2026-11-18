from django.urls import reverse

from bluebottle.activity_links.models import (
    LinkedDateActivity,
    LinkedDeadlineActivity,
    LinkedPeriodicActivity,
    LinkedScheduleActivity,
)
from bluebottle.activity_links.tests.factories import (
    LinkedDateActivityFactory,
    LinkedDateSlotFactory,
    LinkedDeadlineActivityFactory,
    LinkedDeedFactory,
)
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase


class LinkedActivityAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.address = 'Brugstraat 24, 9711 HZ Groningen, Netherlands'
        self.other_address = 'Grote Markt 1, 9712 HN Groningen, Netherlands'
        self.location = GeolocationFactory.create(formatted_address=self.address)
        self.other_location = GeolocationFactory.create(formatted_address=self.other_address)

    def test_list_shows_address(self):
        LinkedDeadlineActivityFactory.create(location=self.location)
        LinkedDeedFactory.create()

        page = self.app.get(reverse('admin:activity_links_linkedactivity_changelist'), user=self.superuser)

        self.assertContains(page, self.address)

    def test_list_shows_distinct_slot_addresses_of_date_activity(self):
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=self.location)
        LinkedDateSlotFactory.create(activity=activity, location=self.location)
        LinkedDateSlotFactory.create(activity=activity, location=self.other_location)

        page = self.app.get(reverse('admin:activity_links_linkedactivity_changelist'), user=self.superuser)

        self.assertContains(page, f'{self.address}, {self.other_address}')

    def test_list_without_location(self):
        LinkedDeedFactory.create()
        LinkedDateActivityFactory.create()

        page = self.app.get(reverse('admin:activity_links_linkedactivity_changelist'), user=self.superuser)

        self.assertEqual(page.status_code, 200)

    def test_deadline_activity_shows_full_address(self):
        activity = LinkedDeadlineActivityFactory.create(location=self.location)

        page = self.app.get(
            reverse('admin:activity_links_linkeddeadlineactivity_change', args=(activity.pk,)),
            user=self.superuser
        )

        self.assertContains(page, self.address)

    def test_date_activity_shows_slot_addresses(self):
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=self.location)

        page = self.app.get(
            reverse('admin:activity_links_linkeddateactivity_change', args=(activity.pk,)),
            user=self.superuser
        )

        self.assertContains(page, self.address)


class LinkedActivityVerboseNamesTestCase(BluebottleTestCase):
    def test_plural_names(self):
        names = {
            model._meta.verbose_name_plural
            for model in (
                LinkedDateActivity, LinkedDeadlineActivity, LinkedPeriodicActivity, LinkedScheduleActivity
            )
        }

        self.assertEqual(
            names,
            {'Date activities', 'Flexible activities', 'Recurring activities', 'Past date activities'}
        )
