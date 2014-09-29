from bluebottle.utils.utils import StatusDefinition
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_donation_model, get_project_model

DONATION_MODEL = get_donation_model()
PROJECT_MODEL = get_project_model()

class DonationModule(DashboardModule):

    title = _('Donations')
    template = 'admin_tools/dashboard/donation_module.html'
    donation_url = '/admin/donations/donation'
    euro_currency = u"\u20AC"
    statuses_to_analyze = [StatusDefinition.SUCCESS, StatusDefinition.PENDING]

    def __init__(self, **kwargs):

        donations = DONATION_MODEL.objects.filter(order__status__in=self.statuses_to_analyze)
        number_of_donations = donations.count()
        total_amount = donations.aggregate(Sum('amount'))['amount__sum']
        number_of_employees = donations.distinct('order__user').count()

        #initialize children
        self.children = ()

        if not total_amount:
            total_amount = '0.00'

        self.append_to_children('Total amount donated', total_amount, self.euro_currency)

        # Because we are in bb and this regards only Booking (but creating a donation app only for this class
        # it's probably too much right now, just remember to do it once we create a donation app in there.
        try:
            booking_amount = PROJECT_MODEL.objects.aggregate(Sum('amount_additional'))['amount_additional__sum']
            self.append_to_children('Total amount matched by Booking', booking_amount, self.euro_currency)
        except:
            pass

        self.append_to_children('Total number of employees who donated', number_of_employees)
        self.append_to_children('Total number of donations', number_of_donations)

        super(DonationModule, self).__init__(**kwargs)

    def append_to_children(self, title, value, currency='', url=donation_url):
        self.children = self.children + ({'title': title, 'value': value, 'currency': currency, 'url': url}, )