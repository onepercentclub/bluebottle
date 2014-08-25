from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.utils.translation import gettext as _
from bluebottle.payments.models import Payment


class MockPaymentStatuses(DjangoChoices):
    created = ChoiceItem('created', label=_("Created"))
    started = ChoiceItem('started', label=_("Started"))
    authorized = ChoiceItem('authorized', label=_("Authorized"))
    settled = ChoiceItem('settled', label=_("Settled"))
    failed = ChoiceItem('failed', label=_("Failed"))
    cancelled = ChoiceItem('cancelled', label=_("Cancelled"))
    chargedback = ChoiceItem('charged_back', label=_("Charged back"))
    refunded = ChoiceItem('refunded', label=_("Refunded"))
    unknown = ChoiceItem('unknown', label=_("Unknown"))


class MockPayment(Payment):

    status = models.CharField(_("Status"), max_length=20, choices=MockPaymentStatuses.choices,
                          default=MockPaymentStatuses.created, db_index=True)