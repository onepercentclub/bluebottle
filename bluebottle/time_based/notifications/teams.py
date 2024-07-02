from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.time_based.messages import get_slot_info


class ManagerTeamNotification(TransitionMessage):
    context = {
        "title": "activity.title",
        "name": "user.full_name",
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url() + f"?teamId={self.obj.pk}"

    action_title = pgettext("email", "Open your team")

    def get_recipients(self):
        """manager"""
        return [self.obj.activity.owner]


class ManagerTeamRemovedNotification(ManagerTeamNotification):
    """
    A participant removed notify owner
    """

    subject = pgettext("email", 'A team has been removed from your activity "{title}"')
    template = "messages/teams/manager_team_removed"


class ManagerTeamWithdrewNotification(ManagerTeamNotification):
    """
    A participant withdrew from your activity
    """

    subject = pgettext("email", 'A team has withdrawn from your activity "{title}"')
    template = "messages/teams/manager_team_withdrew"


class UserTeamNotification(TransitionMessage):
    context = {
        "title": "activity.title",
        "name": "user.full_name",
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url() + f"?teamId={self.obj.pk}"

    action_title = pgettext("email", "View team")

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class UserTeamRemovedNotification(UserTeamNotification):
    """
    The participant was removed from the activity
    """

    subject = pgettext("email", 'Your team was removed from the activity "{title}"')
    template = "messages/teams/user_team_removed"


class UserTeamWithdrewNotification(UserTeamNotification):
    """
    Team withdrew from activity
    """

    subject = pgettext("email", 'You withdrew your team from the activity "{title}"')
    template = "messages/teams/user_team_withdrew"


class UserTeamScheduledNotification(UserTeamNotification):
    """
    Team is scheduled for activity
    """

    subject = pgettext(
        "email", 'Your team has been scheduled for the activity "{title}"'
    )
    template = "messages/teams/user_team_scheduled"

    def get_slot(self):
        return self.obj.slots.first()

    def get_event_data(self, recipient=None):
        return self.get_slot().event_data

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context["slot"] = get_slot_info(self.get_slot())
        return context


class CaptainTeamMemberNotification(TransitionMessage):
    context = {
        "title": "team.activity.title",
        "name": "user.full_name",
    }

    @property
    def action_link(self):
        return self.obj.team.activity.get_absolute_url() + f"?teamId={self.obj.team.pk}"

    action_title = pgettext("email", "Open your team")

    def get_recipients(self):
        """manager"""
        return [self.obj.team.user]


class CaptainTeamMemberJoinedNotification(CaptainTeamMemberNotification):
    """
    A team member joined notify owner
    """

    subject = pgettext(
        "email", 'A participant has joined your team for the activity "{title}"'
    )
    template = "messages/teams/captain_teammember_joined"


class CaptainTeamMemberRemovedNotification(CaptainTeamMemberNotification):
    """
    A team member removed notify owner
    """

    subject = pgettext(
        "email",
        'A participant has been removed from your team for the activity "{title}"',
    )
    template = "messages/teams/captain_teammember_removed"


class CaptainTeamMemberWithdrewNotification(CaptainTeamMemberNotification):
    """
    A team member withdrew from your team
    """

    subject = pgettext(
        "email", 'A participant has withdrawn from your team for the activity "{title}"'
    )
    template = "messages/teams/captain_teammember_withdrew"


class UserTeamMemberNotification(TransitionMessage):
    context = {
        "title": "team.activity.title",
        "name": "team.user.full_name",
    }

    @property
    def action_link(self):
        return self.obj.team.activity.get_absolute_url() + f"?teamId={self.obj.team.pk}"

    action_title = pgettext("email", "View team")

    def get_recipients(self):
        """participant"""
        return [self.obj.user]


class UserTeamMemberJoinedNotification(UserTeamMemberNotification):
    """
    The participant joined your team
    """

    subject = pgettext("email", 'You joined {name}\'s team for the activity "{title}"')
    template = "messages/teams/user_teammember_joined"


class UserTeamMemberRemovedNotification(UserTeamMemberNotification):
    """
    The participant was removed from the activity
    """

    subject = pgettext(
        "email", 'You have been removed from {name}\'s team for the activity "{title}"'
    )
    template = "messages/teams/user_teammember_removed"


class UserTeamMemberWithdrewNotification(UserTeamMemberNotification):
    """
    The participant was removed from the team
    """

    subject = pgettext(
        "email", 'You have withdrawn from {name}\'s team for the activity "{title}"'
    )
    template = "messages/teams/user_teammember_withdrew"


class UserTeamMemberScheduledNotification(UserTeamNotification):
    """
    Your team has been scheduled for activity
    """

    subject = pgettext(
        "email", 'Your team has been scheduled for the activity "{title}"'
    )
    template = "messages/teams/user_teammember_scheduled"

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context["slot"] = get_slot_info(self.obj.team.slots.first())
        return context


class UserTeamMemberChangedNotification(TransitionMessage):
    """
    The date/time for your team has been changed
    """

    subject = pgettext(
        "email", 'The date or location for your team has been changed for the activity "{title}"'
    )

    template = "messages/teams/user_teamslot_changed"

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context["slot"] = get_slot_info(self.obj.team.slots.first())
        context["name"] = recipient.first_name
        return context

    context = {
        "title": "activity.title",
    }

    def get_event_data(self, recipient):
        return self.obj.event_data

    @property
    def action_link(self):
        team = self.obj.team
        activity = team.activity
        return activity.get_absolute_url() + f"?teamId={team.pk}"

    action_title = pgettext("email", "View team")

    def get_recipients(self):
        """participants"""
        return [p.user for p in self.obj.accepted_participants.all()]
