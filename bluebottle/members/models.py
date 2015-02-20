from bluebottle.bb_accounts.models import BlueBottleBaseUser


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_member', 'change_member', 'delete_member',
        )
    }
}

class Member(BlueBottleBaseUser):
    pass
