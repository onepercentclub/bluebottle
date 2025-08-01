import logging
from builtins import str
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.grant_management.effects import GenerateGrantPaymentEffect
from bluebottle.grant_management.models import GrantProvider

logger = logging.getLogger(__name__)


class CreateGrantPaymentTask(ModelPeriodicTask):

    def get_queryset(self):
        current_date = now()
        current_week = current_date.isocalendar()[1]
        all_providers = GrantProvider.objects.all()
        matching_providers = []
        for provider in all_providers:
            frequency = int(provider.payment_frequency)
            if current_week % frequency == 0:
                matching_providers.append(provider.id)

        return GrantProvider.objects.filter(id__in=matching_providers)

    effects = [
        GenerateGrantPaymentEffect
    ]

    def __str__(self):
        return str(_("Create payment for provider with approved payouts."))


GrantProvider.periodic_tasks = [CreateGrantPaymentTask]
