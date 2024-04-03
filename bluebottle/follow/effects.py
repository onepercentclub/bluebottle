from django.utils.translation import gettext_lazy as _

from bluebottle.follow.models import follow, unfollow
from bluebottle.fsm.effects import Effect


class FollowActivityEffect(Effect):
    "Follow the activity"

    template = 'admin/follow_effect.html'

    def execute(self, **kwargs):
        if self.instance.user:
            follow(self.instance.user, self.instance.activity)

    def __repr__(self):
        return '<Effect: Follow {} by {}>'.format(self.instance.activity, self.instance.user)

    def __str__(self):
        user = self.instance.user
        if not self.instance.user.id:
            user = self.instance.user.full_name
        return _('Follow {activity} by {user}').format(activity=self.instance.activity, user=user)


class UnFollowActivityEffect(Effect):
    "Unfollow the activity"

    template = 'admin/unfollow_effect.html'

    def execute(self, **kwargs):
        if self.instance.user:
            unfollow(self.instance.user, self.instance.activity)

    def __repr__(self):
        return '<Effect: Unfollow {} by {}>'.format(self.instance.activity, self.instance.user)

    def __str__(self):
        user = self.instance.user
        if not self.instance.user.id:
            user = self.instance.user.full_name
        return _('Unfollow {activity} by {user}').format(activity=self.instance.activity, user=user)
