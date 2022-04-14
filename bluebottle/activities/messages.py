from pytz import timezone

from django.urls import reverse
from django.template.defaultfilters import time, date

from bluebottle.initiatives.models import InitiativePlatformSettings
from django.utils.timezone import get_current_timezone

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import pgettext_lazy as pgettext
from bluebottle.utils.utils import get_current_host, get_current_language


class ActivityWallpostOwnerMessage(TransitionMessage):
    subject = pgettext('email', "You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner'

    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """activity organizer"""
        if self.obj.author != self.obj.content_object.owner:
            return [self.obj.content_object.owner]
        else:
            return []


class ActivityWallpostReactionMessage(TransitionMessage):
    subject = pgettext('email', "You have a new post on '{title}'")
    template = 'messages/activity_wallpost_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }
    action_title = pgettext('email', 'View response')

    def get_recipients(self):
        """wallpost author"""
        return [self.obj.wallpost.author]


class ActivityWallpostOwnerReactionMessage(TransitionMessage):
    subject = pgettext('email', "You have a new post on '{title}'")
    template = 'messages/activity_wallpost_owner_reaction'

    context = {
        'title': 'wallpost.content_object.title'
    }

    def get_recipients(self):
        """activity organizer"""
        if self.obj.author != self.obj.wallpost.content_object.owner:
            return [self.obj.wallpost.content_object.owner]
        else:
            return []


class ActivityWallpostFollowerMessage(TransitionMessage):
    subject = pgettext('email', "Update from '{title}'")
    template = 'messages/activity_wallpost_follower'
    context = {
        'title': 'content_object.title'
    }

    def get_recipients(self):
        """followers of the activity"""
        activity = self.obj.content_object
        follows = activity.follows.filter(
            user__campaign_notifications=True
        ).exclude(
            user__in=(self.obj.author, self.obj.content_object.owner)
        )

        return [follow.user for follow in follows]


class ActivityNotification(TransitionMessage):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['impact'] = InitiativePlatformSettings.load().enable_impact

        return context

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ImpactReminderMessage(ActivityNotification):
    subject = pgettext('email', 'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_impact_reminder'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [self.obj.owner]


class ActivitySucceededNotification(ActivityNotification):
    """
    The activity succeeded
    """
    subject = pgettext('email', 'Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_succeeded'


class ActivityRestoredNotification(ActivityNotification):
    """
    The activity was restored
    """
    subject = pgettext('email', 'The activity "{title}" has been restored')
    template = 'messages/activity_restored'


class ActivityRejectedNotification(ActivityNotification):
    """
    The activity was rejected
    """
    subject = pgettext('email', 'Your activity "{title}" has been rejected')
    template = 'messages/activity_rejected'


class ActivityCancelledNotification(ActivityNotification):
    """
    The activity got cancelled
    """
    subject = pgettext('email', 'Your activity "{title}" has been cancelled')
    template = 'messages/activity_cancelled'


class ActivityExpiredNotification(ActivityNotification):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = pgettext('email', 'The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_expired'


class ParticipantWithdrewConfirmationNotification(ActivityNotification):
    """
    The participant withdrew from the activity
    """
    context = {
        'title': 'activity.title',
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    subject = pgettext('email', 'You have withdrawn from the activity "{title}"')
    template = 'messages/participant_withdrew_confirmation'

    def get_recipients(self):
        """wallpost author"""
        return [self.obj.user]


class MatchingActivitiesNotification(TransitionMessage):
    """
    Send a list of matching initiaives to user
    """
    subject = pgettext(
        'email',
        '{first_name}, there are {count} activities on {site_name} matching your profile'
    )
    template = 'messages/matching_activities'

    @property
    def action_link(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/initiatives/activities/list".format(
            domain, language
        )

    action_title = pgettext('email', 'View more activities')

    def get_recipients(self):
        """user"""
        return [self.obj]

    def get_activity_context(self, activity):
        from bluebottle.time_based.models import DateActivity

        context = {
            'title': activity.title,
            'url': activity.get_absolute_url(),
            'image': (
                reverse('activity-image', args=(activity.pk, '200x200'))
                if activity.image else
                reverse('initiative-image', args=(activity.initiative.pk, '200x200'))
            ),
            'expertise': activity.expertise.name if activity.expertise else None,
            'theme': activity.initiative.theme.name,
        }
        if isinstance(activity, DateActivity):
            slots = activity.slots.filter(status='open')
            context['is_online'] = all(
                slot.is_online for slot in slots
            )
            if not context['is_online']:
                locations = set(str(slot.location) for slot in slots)
                if len(locations) == 1:
                    context['location'] = locations[0]
                else:
                    context['location'] = pgettext('email', 'Multiple locations')

            if len(slots) > 1:
                context['when'] = pgettext('email', 'Mutliple time slots')
            else:
                slot = slots[0]

                if slot.location and not slot.is_online:
                    tz = timezone(slot.location.timezone)
                else:
                    tz = get_current_timezone()

                start = '{} {}'.format(
                    date(slot.start.astimezone(tz)), time(slot.start.astimezone(tz))
                ) if slot.start else pgettext('email', 'Starts immediately')
                end = '{} {}'.format(
                    date(slot.end.astimezone(tz)), time(slot.end)
                ) if slot.end else pgettext('email', 'runs indefinitely')
                context['when'] = '{start_date} {start_time} - {end_time} ({timezone})'.format(
                    start_date=date(slot.start.astimezone(tz)),
                    start_time=time(slot.start.astimezone(tz)),
                    end_time=time(slot.end.astimezone(tz)),
                    timezone=start.strftime('%Z')
                )

                context['when'] = '{} - {}'.format(start, end)
        else:
            if activity.is_online:
                context['is_online'] = True
            else:
                context['location'] = activity.location

            start = date(activity.start) if activity.start else pgettext('email', 'starts immediately')
            end = date(activity.deadline) if activity.deadline else pgettext('email', 'runs indefinitely')

            context['when'] = '{} - {}'.format(start, end)

        return context

    def get_context(self, recipient, activities=None):
        context = super().get_context(recipient)
        context['profile_incomplete'] = (
            not (len(recipient.favourite_themes.all())) or
            not (len(recipient.skills.all())) or
            not (recipient.place or recipient.location)
        )
        if activities:
            context['activities'] = [
                self.get_activity_context(activity) for activity in activities[:3]
            ]
            context['count'] = len(activities)

        return context


class TeamNotification(ActivityNotification):
    context = {
        'title': 'activity.title',
        'team_captain_email': 'owner.email',
        'team_name': 'name'
    }

    @property
    def action_link(self):
        return self.obj.activity.get_absolute_url()

    action_title = pgettext('email', 'View activity')

    def get_recipients(self):
        """acitvity mananager"""
        return [self.obj.activity.owner]


class TeamAddedMessage(TeamNotification):
    subject = pgettext('email', "A new team has joined '{title}'")
    template = 'messages/team_added'


class TeamAppliedMessage(TeamNotification):
    subject = pgettext('email', "A new team has applied to '{title}'")
    template = 'messages/team_applied'


class TeamAcceptedMessage(TeamNotification):
    subject = pgettext('email', "Your team has been accepted for '{title}'")
    template = 'messages/team_accepted'

    def get_recipients(self):
        """team captain"""
        return [self.obj.owner]


class TeamCancelledMessage(TeamNotification):
    subject = pgettext('email', "Your team was cancelled")
    template = 'messages/team_cancelled'

    def get_recipients(self):
        """team participants"""
        return [contributor.user for contributor in self.obj.members.all()]


class TeamReopenedMessage(TeamNotification):
    subject = pgettext('email', "Your team was accepted again")
    template = 'messages/team_reopened'

    def get_recipients(self):
        """team participants"""
        return [contributor.user for contributor in self.obj.members.all()]
