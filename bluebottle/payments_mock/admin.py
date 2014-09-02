from bluebottle.payments_mock.models import MockPayment
from polymorphic.admin import PolymorphicChildModelAdmin


class MockPaymentAdmin(PolymorphicChildModelAdmin):
    model = MockPayment