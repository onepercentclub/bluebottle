from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.utils.translation import gettext as _
from bluebottle.payments.models import Payment


class MockPaymentStatuses(DjangoChoices):
    pass


class MockPayment(Payment):
    pass