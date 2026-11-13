from django.utils.translation import gettext as _

from bluebottle.cta.framework import ActionItem, ActionType, registry
from bluebottle.cta.types.base import demo_enabled


class DemoActionType(ActionType):
    def get_items(self, user):
        if demo_enabled():
            yield self.item()

    def item(self):
        raise NotImplementedError()


@registry.register
class ThankParticipants(DemoActionType):
    slug = 'thank_participants'
    audience = 'manager'
    group = 'wrap_up'
    priority = 60

    def item(self):
        return ActionItem(
            type=self.slug, object_id=900001, group=self.group, severity='info',
            title=_('Beach clean-up (demo)'),
            message=_('This activity just ended. Thank your participants and share the result.'),
            url='/activities/manage', count=12, is_demo=True,
        )


@registry.register
class LowEngagement(DemoActionType):
    slug = 'low_engagement'
    audience = 'manager'
    group = 'participation'
    priority = 35

    def item(self):
        return ActionItem(
            type=self.slug, object_id=900002, group=self.group, severity='attention',
            title=_('Neighbourhood lunch (demo)'),
            message=_('Nobody has signed up 7 days after publishing. Try sharing it with a team.'),
            url='/activities/manage', is_demo=True,
        )


@registry.register
class NewMemberSignups(DemoActionType):
    slug = 'new_member_signups'
    audience = 'platform_manager'
    group = 'participation'
    priority = 45

    def item(self):
        return ActionItem(
            type=self.slug, object_id=900003, group=self.group, severity='info',
            title=_('New members (demo)'),
            message=_('8 members joined this week without joining an activity yet. Send them a welcome.'),
            url='/', count=8, is_demo=True,
        )


@registry.register
class ReportedContent(DemoActionType):
    slug = 'reported_content'
    audience = 'platform_manager'
    group = 'decision'
    priority = 8

    def item(self):
        return ActionItem(
            type=self.slug, object_id=900004, group=self.group, severity='urgent',
            title=_('Reported content (demo)'),
            message=_('2 updates were reported by members and need moderation.'),
            url='/', count=2, is_demo=True,
        )
