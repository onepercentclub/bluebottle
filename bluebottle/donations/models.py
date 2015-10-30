from bluebottle.bb_donations.models import BaseDonation

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}


class Donation(BaseDonation):

    def __unicode__(self):
        return u'{} for {}'.format(self.amount, self.project)


from .signals import *
