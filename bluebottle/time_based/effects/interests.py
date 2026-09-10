from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import Interest


class DeleteInterestEffect(Effect):
    """
    Remove any Interest row for this user on the activity or slot.

    Used when the user successfully joins or applies, so interest does not
    linger alongside a real registration/participant.
    """

    title = _('Delete matching interest')
    template = 'admin/delete_interest.html'

    def matching_interest_exists(self):
        """User has expressed interest in this activity or slot"""
        return self._queryset().exists()

    conditions = [matching_interest_exists]

    def _queryset(self):
        instance = self.instance
        user = instance.user
        slot_id = getattr(instance, 'slot_id', None)
        if slot_id:
            return Interest.objects.filter(user=user, slot_id=slot_id)
        return Interest.objects.filter(
            user=user,
            activity_id=instance.activity_id,
            slot__isnull=True,
        )

    def post_save(self, **kwargs):
        self._queryset().delete()

    def __str__(self):
        return _('Delete matching interest')
