from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.follow.models import follow, unfollow


class FollowActivityEffect(Effect):
    "Follow the activity"

    post_save = True

    def execute(self, **kwargs):
        follow(self.instance.user, self.instance.activity)

    def __repr__(self):
        return '<Effect: Follow {} by {}>'.format(self.instance.activity, self.instance.user)

    def __unicode__(self):
        return _('Follow %s by %s') % (self.instance.activity, self.instance.user)


class UnFollowActivityEffect(Effect):
    "Unfollow the activity"

    post_save = True

    def execute(self, **kwargs):
        unfollow(self.instance.user, self.instance.activity)

    def __repr__(self):
        return '<Effect: Unfollow {} by {}>'.format(self.instance.activity, self.instance.user)

    def __unicode__(self):
        return _('Unfollow %s by %s') % (self.instance.activity, self.instance.user)
