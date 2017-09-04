from bluebottle.bb_fundraisers.models import BaseFundraiser
from bluebottle.clients import properties


class Fundraiser(BaseFundraiser):
    def get_absolute_url(self):
        """ Get the URL for the current fundraiser. """
        return 'https://{}/fundraisers/{}'.format(properties.tenant.domain_url, self.id)
