from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.utils.translation import gettext as _
from bluebottle.payments.models import Payment


class MockPayment(Payment):
    pass

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Mock Payment"
        verbose_name_plural = "Mock Payments"
