from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_donation_model

DONATION_MODEL = get_donation_model()

class DonationModule(DashboardModule):

    title = _('Donations')
    template = 'admin_tools/dashboard/donation_module.html'


    def __init__(self, **kwargs):
        donation_url = '/admin/donations/donation'
        self.children = (
            # Metrics Donations
            {'title': 'Total amount donated', 'value': DONATION_MODEL.objects.count(), 'url': donation_url},

            # TODO
            {'title': 'Total amount matched by Booking', 'value': DONATION_MODEL.objects.count(), 'url': donation_url},
            {'title': 'Total number of donations', 'value': DONATION_MODEL.objects.count(), 'url': donation_url},
            {'title': 'Total number of employees who donated', 'value': DONATION_MODEL.objects.count(), 'url': donation_url},

            # Sort metrics per region (for loop?)
            {'title': 'Africa', 'value': DONATION_MODEL.objects.count()},
            {'title': 'Americas', 'value': DONATION_MODEL.objects.count()},
            {'title': 'Asia', 'value': DONATION_MODEL.objects.count()},
            {'title': 'Europe', 'value': DONATION_MODEL.objects.count()},
            {'title': 'Oceania', 'value': DONATION_MODEL.objects.count()},

            # Sort metrics per project (for loop?)
            
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