from bluebottle.payments.models import Payment
from bluebottle.payments_mock.models import MockPayment
from polymorphic.admin import PolymorphicChildModelAdmin


class MockPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = MockPayment