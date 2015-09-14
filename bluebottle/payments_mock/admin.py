from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from bluebottle.payments_mock.models import MockPayment


class MockPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = MockPayment
