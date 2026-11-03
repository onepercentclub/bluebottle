from datetime import timedelta

from django.utils.timezone import now
from moneyed import Money

from bluebottle.grant_management.documents import GrantApplicationDocument
from bluebottle.grant_management.models import GrantDonor
from bluebottle.grant_management.tests.factories import (
    GrantApplicationFactory,
    GrantDonorFactory,
    GrantFundFactory,
)
from bluebottle.test.utils import BluebottleTestCase


class GrantApplicationDocumentTestCase(BluebottleTestCase):
    def test_prepare_dates_uses_started(self):
        started = now() - timedelta(days=2)
        application = GrantApplicationFactory.create(started=started)

        document = GrantApplicationDocument()
        dates = document.prepare_dates(application)

        self.assertEqual(dates, [{'start': started, 'end': started}])
        self.assertEqual(document.prepare_start(application), [started])
        self.assertEqual(document.prepare_end(application), [started])

    def test_prepare_dates_falls_back_to_grant_donor_created(self):
        application = GrantApplicationFactory.create(started=None)
        application.created = now() - timedelta(days=30)
        application.save()

        donor = GrantDonorFactory.create(
            activity=application,
            fund=GrantFundFactory.create(),
            amount=Money(100, 'EUR'),
            payout=None,
        )
        donor.created = now() - timedelta(days=3)
        donor.save()

        application.started = None
        application.save(update_fields=['started'])
        application.refresh_from_db()

        document = GrantApplicationDocument()
        dates = document.prepare_dates(application)

        self.assertEqual(dates, [{'start': donor.created, 'end': donor.created}])

    def test_prepare_dates_falls_back_to_created(self):
        created = now() - timedelta(days=10)
        application = GrantApplicationFactory.create(started=None)
        application.created = created
        application.save()
        GrantDonor.objects.filter(activity=application).delete()

        document = GrantApplicationDocument()
        dates = document.prepare_dates(application)

        self.assertEqual(dates, [{'start': created, 'end': created}])
