from bluebottle.utils.utils import StatusDefinition
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from admin_tools.dashboard.modules import DashboardModule
from bluebottle.utils.model_dispatcher import get_donation_model

DONATION_MODEL = get_donation_model()


class DonationModule(DashboardModule):

    title = _('Donations')
    template = 'admin_tools/dashboard/donation_module.html'
    donation_url = '/admin/donations/donation'

    def __init__(self, **kwargs):

        # import ipdb;ipdb.set_trace()

        donations = DONATION_MODEL.objects.filter(order__status=StatusDefinition.SUCCESS)
        donation_url = '/admin/donations/donation'
        number_of_donations = donations.count()
        total_amount = donations.aggregate(Sum('amount'))['amount__sum']
        number_of_employees = donations.distinct('order__user').count()

        #cd.filter(order__user__office__country__subregion__region='Europe')
        # cd[1].order.user.office.country.subregion.region

        # sort_europe = donations.filter(order__user__office__country__subregion__region__name="Europe").count()
        # sort_africa = donations.filter(order__user__office__country__subregion__region__name="Africa").count()
        # sort_americas = donations.filter(order__user__office__country__subregion__region__name="Americas").count()
        # sort_oceania = donations.filter(order__user__office__country__subregion__region__name="Oceania").count()
        # sort_asia = donations.filter(order__user__office__country__subregion__region__name="Asia").count()

        # office country subregio regio
        self.children = (
            # Metrics Donations
            {'title': 'Total amount donated', 'value': total_amount, 'url': donation_url},
            {'title': 'Total amount matched by Booking', 'value': 'TODO', 'url': donation_url},
            {'title': 'Total number of employees who donated', 'value': number_of_employees, 'url': donation_url},
            {'title': 'Total number of donations', 'value': number_of_donations, 'url': donation_url},
            # Sort metrics per region (for loop?)
            # {'title': 'Africa', 'value': sort_africa, 'url': self.donation_url},
            # {'title': 'Americas', 'value': sort_americas, 'url': self.donation_url},
            # {'title': 'Asia', 'value': sort_asia, 'url': self.donation_url},
            # {'title': 'Europe', 'value': sort_europe, 'url': self.donation_url},
            # {'title': 'Oceania', 'value': sort_oceania, 'url': self.donation_url},

            # Sort metrics per project (for loop?)
            # donation order user office
        )
        super(DonationModule, self).__init__(**kwargs)