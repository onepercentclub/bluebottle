import unittest
from datetime import datetime

from django.test import TestCase
from django_fsm.db.fields import TransitionNotAllowed

from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.models import TestBaseUser
from bluebottle.test.utils import FsmTestMixin

from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import StatusDefinition

from mock import patch

class PaymentsDocdataTestCase(TestCase, FsmTestMixin):
    def setUp(self):
        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='mock')
        self.service = PaymentService(order_payment=self.order_payment)

    def test_check_authorized_status(self):
        # Check that the status propagated through to order
        self.assert_status(self.order_payment.payment, StatusDefinition.STARTED)
        self.assert_status(self.order_payment, StatusDefinition.STARTED)
        self.assert_status(self.order, StatusDefinition.LOCKED)
