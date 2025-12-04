from datetime import timedelta

from django.db.models import Sum, Q
from django.template.defaultfilters import time, date
from django.urls import reverse
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import pgettext_lazy as pgettext
from pytz import timezone

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.notifications.models import Message
from bluebottle.utils.utils import get_current_host, get_current_language


class MatchingActivitiesNotification(TransitionMessage):
    """
    Send a list of matching activities to user
    """
    subject = pgettext(
        'email',
        '{first_name}, there are {count} activities on {site_name} matching your profile'
    )
    template = 'messages/matching/matching_activities'

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
            "title": activity.title,
            "url": activity.get_absolute_url(),
            "image": (
                reverse("activity-image", args=(activity.pk, "200x200"))
                if activity.image
                else reverse(
                    "initiative-image", args=(activity.initiative.pk, "200x200")
                )
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


class BaseDoGoodHoursReminderNotification(TransitionMessage):
    """
    Base class for all notifications do-good hours reminders.
    """

    class Meta:
        abstract = True

    @property
    def action_link(self):
        from bluebottle.clients.utils import tenant_url
        return tenant_url('/initiatives/activities/list')

    action_title = pgettext('email', 'Find activities')

    send_once = True

    def get_context(self, recipient):
        from bluebottle.members.models import MemberPlatformSettings
        from bluebottle.clients.utils import tenant_url

        context = super(BaseDoGoodHoursReminderNotification, self).get_context(recipient)
        settings = MemberPlatformSettings.load()
        context['do_good_hours'] = settings.do_good_hours
        context['opt_out_link'] = tenant_url('/member/profile')
        return context

    @property
    def generic_subject(self):
        from bluebottle.members.models import MemberPlatformSettings
        settings = MemberPlatformSettings.load()
        context = self.get_generic_context()
        context['do_good_hours'] = settings.do_good_hours
        return str(self.subject.format(**context))

    def already_send(self, recipient):
        return Message.objects.filter(
            template=self.get_template(),
            recipient=recipient,
            sent__year=now().year
        ).count() > 0

    def get_recipients(self):
        """members with do good hours"""
        from bluebottle.members.models import Member
        from bluebottle.members.models import MemberPlatformSettings

        year = now().year
        do_good_hours = timedelta(hours=MemberPlatformSettings.load().do_good_hours)

        members = Member.objects.annotate(
            hours=Sum(
                'contributor__contributions__timecontribution__value',
                filter=(
                    Q(contributor__contributions__start__year=year) &
                    Q(contributor__contributions__status__in=['new', 'succeeded'])
                )
            ),
        ).filter(
            Q(hours__lt=do_good_hours) | Q(hours__isnull=True),
            is_active=True,
            receive_reminder_emails=True
        ).distinct()
        return members


class DoGoodHoursReminderQ1Notification(BaseDoGoodHoursReminderNotification):
    """
    Send a reminder in Q1 to platform user to spend their do-good hours.
    """
    subject = pgettext('email', "It’s a new year, let's make some impact!")
    template = 'messages/matching/reminder-q1'


class DoGoodHoursReminderQ2Notification(BaseDoGoodHoursReminderNotification):
    """
    Send a reminder in Q2 to platform user to spend their do-good hours.
    """
    subject = pgettext('email', "Haven’t joined an activity yet? Let’s get started!")
    template = 'messages/matching/reminder-q2'


class DoGoodHoursReminderQ3Notification(BaseDoGoodHoursReminderNotification):
    """
    Send a reminder in Q3 to platform user to spend their do-good hours.
    """
    subject = pgettext('email', "Half way through the year and still plenty of activities to join")
    template = 'messages/matching/reminder-q3'


class DoGoodHoursReminderQ4Notification(BaseDoGoodHoursReminderNotification):
    """
    Send a reminder in Q4 to platform user to spend their do-good hours.
    """
    subject = pgettext('email', "Make use of your {do_good_hours} hours of impact!")
    template = 'messages/matching/reminder-q4'
