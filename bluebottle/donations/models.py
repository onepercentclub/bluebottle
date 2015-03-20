from bluebottle.bb_donations.models import BaseDonation
from bluebottle.journals.models import update_related_model_when_journal_is_saved

from django.db.models.signals import post_save
from django.dispatch import receiver


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}


class Donation(BaseDonation):

    def __unicode__(self):
        return '{} for {}'.format(self.amount, self.project)


@receiver(post_save, weak=False, sender=Donation)
def create_donation_journal_after_donation_is_changed(sender, instance, created, **kwargs):
    update_related_model_when_journal_is_saved(sender=sender, instance=instance, created=created)
