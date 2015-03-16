from bluebottle.bb_donations.models import BaseDonation


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}


class Donation(BaseDonation):
    pass
