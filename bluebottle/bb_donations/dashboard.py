from bluebottle.utils.utils import StatusDefinition
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_donation_model

DONATION_MODEL = get_donation_model()

class DonationModule(DashboardModule):

    title = _('Donations')
    template = 'admin_tools/dashboard/donation_module.html'


    def __init__(self, **kwargs):
        donation_url = '/admin/donations/donation'

        import ipdb;ipdb.set_trace()

        successful_donations = DONATION_MODEL.objects.filter(order__status=StatusDefinition.SUCCESS)
        number_of_donations = successful_donations.count()
        total_amount = successful_donations.aggregate(Sum('amount'))['amount__sum']
        number_of_employees = successful_donations.distinct('order__user').count()
        #cd.filter(order__user__office__country__subregion__region='Europe')
        # cd[1].order.user.office.country.subregion.region

        # office country subregio regio
        self.children = (
            # Metrics Donations
            {'title': 'Total amount donated', 'value': total_amount, 'url': donation_url},
            {'title': 'Total amount matched by Booking', 'value': 'TODO', 'url': donation_url},
            {'title': 'Total number of employees who donated', 'value': number_of_employees, 'url': donation_url},
            {'title': 'Total number of donations', 'value': number_of_donations, 'url': donation_url},

            # Sort metrics per region (for loop?)
            {'title': 'Africa', 'value': 'TODO'},
            {'title': 'Americas', 'value': 'TODO'},
            {'title': 'Asia', 'value': 'TODO'},
            {'title': 'Europe', 'value': 'TODO'},
            {'title': 'Oceania', 'value': 'TODO'},

            # Sort metrics per project (for loop?)
            # donation order user office
        )


        super(DonationModule, self).__init__(**kwargs)

# Sort metrics per region:
# Africa
# Americas
# Asia
# Europe
# Oceania
#
# Sort metrics per project:
# Project A
# Project B