from bluebottle.bb_fundraisers.models import BaseFundraiser


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_fundraiser', 'change_fundraiser', 'delete_fundraiser',
        )
    }
}

class Fundraiser(BaseFundraiser):
    pass
