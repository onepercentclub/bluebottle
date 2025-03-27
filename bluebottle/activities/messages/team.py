from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class TeamNotification(TransitionMessage):
    context = {
        'title': 'activity.title',
        'team_captain_email': 'owner.email',
        'team_name': 'name',
        'team_captain_name': 'owner.full_name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """activity manager"""
        return [self.obj.activity.owner]


class TeamAddedMessage(TeamNotification):
    subject = pgettext('email', 'A new team has joined "{title}"')
    template = 'messages/team_added'


class TeamAppliedMessage(TeamNotification):
    subject = pgettext('email', 'A new team has applied to "{title}"')
    template = 'messages/team_applied'


class TeamCaptainAcceptedMessage(TeamNotification):
    subject = pgettext('email', 'Your team has been accepted for "{title}"')
    template = 'messages/team_captain_accepted'

    context = {
        'title': 'activity.title',
        'team_captain_email': 'team.owner.email',
        'team_name': 'team.name'
    }

    def get_recipients(self):
        """team captain"""
        return [self.obj.user]


class TeamCancelledMessage(TeamNotification):
    subject = pgettext('email', "Team cancellation for '{title}'")
    template = 'messages/team_cancelled'

    def get_recipients(self):
        """team participants"""
        return [
            contributor.user for contributor in self.obj.members.all() if not contributor.user == self.obj.owner
        ]


class TeamCancelledTeamCaptainMessage(TeamNotification):
    subject = pgettext('email', 'Your team has been rejected for "{title}"')
    template = 'messages/team_cancelled_team_captain'

    context = {
        'title': 'activity.title',
        'team_captain_email': 'team.owner.email',
        'team_name': 'team.name'
    }

    def get_recipients(self):
        """team captain"""
        return [self.obj.user]


class TeamWithdrawnMessage(TeamNotification):
    subject = pgettext('email', "Team cancellation for '{title}'")
    template = 'messages/team_withdrawn'

    def get_recipients(self):
        """team participants"""
        return [contributor.user for contributor in self.obj.members.all()]


class TeamReappliedMessage(TeamNotification):
    subject = pgettext('email', "You’re added to a team for '{title}'")
    template = 'messages/team_reapplied'

    def get_recipients(self):
        """team participants"""
        return [
            contributor.user for contributor in self.obj.members.all()
            if contributor.user != contributor.team.owner
        ]


class TeamWithdrawnActivityOwnerMessage(TeamNotification):
    subject = pgettext('email', "Team cancellation for '{title}'")
    template = 'messages/team_withdrawn_activity_owner'

    def get_recipients(self):
        """team participants"""
        return [self.obj.activity.owner]


class TeamReopenedMessage(TeamNotification):
    subject = pgettext('email', "Your team was accepted again")
    template = 'messages/team_reopened'

    def get_recipients(self):
        """team participants"""
        return [contributor.user for contributor in self.obj.members.all()]


class TeamMemberAddedMessage(TeamNotification):
    subject = pgettext('email', 'Someone has joined your team for "{title}"')
    template = 'messages/team_member_added'

    context = {
        'name': 'user.full_name',
        'title': 'activity.title',
    }
    action_title = pgettext('email', 'View activity')

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    def get_recipients(self):
        """team captain"""
        if self.obj.accepted_invite and self.obj.accepted_invite.contributor.team:
            return [self.obj.accepted_invite.contributor.team.owner]
        else:
            return []


class TeamMemberWithdrewMessage(TeamNotification):
    subject = pgettext('email', 'A participant has withdrawn from your team for "{title}"')
    template = 'messages/team_member_withdrew'

    context = {
        'name': 'user.full_name',
        'title': 'activity.title',
    }
    action_title = pgettext('email', 'View activity')

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    def get_recipients(self):
        """team captain"""
        if self.obj.team and self.obj.user != self.obj.team.owner:
            return [self.obj.team.owner]
        else:
            return []


class TeamMemberRemovedMessage(TeamNotification):
    subject = pgettext('email', "Team member removed for ‘{title}’")
    template = 'messages/team_member_removed'

    context = {
        'name': 'user.full_name',
        'title': 'activity.title',
    }
    action_title = pgettext('email', 'View activity')

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    def get_recipients(self):
        """team captain"""
        if self.obj.team and self.obj.user != self.obj.team.owner:
            return [self.obj.team.owner]
        else:
            return []
