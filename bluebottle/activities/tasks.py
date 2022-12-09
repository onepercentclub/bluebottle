import logging
from datetime import date, datetime

from celery.schedules import crontab
from celery.task import periodic_task
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from elasticsearch_dsl.query import Nested, Q, FunctionScore, ConstantScore, MatchAll

from bluebottle.activities.documents import activity
from bluebottle.activities.messages import MatchingActivitiesNotification, DoGoodHoursReminderQ1Notification, \
    DoGoodHoursReminderQ4Notification, DoGoodHoursReminderQ3Notification, DoGoodHoursReminderQ2Notification
from bluebottle.activities.models import Activity, Contributor
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member, MemberPlatformSettings

logger = logging.getLogger('bluebottle')


def get_matching_activities(user):
    search = activity.search().filter(
        Q('terms', status=['open', 'running']) &
        Q('terms', type=['dateactivity', 'periodactivity'])
    )

    query = ConstantScore(
        boost=.5,
        filter=Nested(
            path='theme',
            query=Q(
                'terms',
                theme__id=[
                    theme.pk for theme in user.favourite_themes.all()
                ]
            )
        )
    ) | ConstantScore(
        filter=Q('term', is_online=True)
    )

    skills = user.skills.all()
    if skills:
        query = query | ConstantScore(
            filter=Nested(
                path='expertise',
                query=Q(
                    'terms',
                    expertise__id=[
                        skill.pk for skill in user.skills.all()
                    ]
                )
            )
        ) | ConstantScore(
            boost=0.75,
            filter=~Nested(
                path='expertise',
                query=Q(
                    'exists',
                    field='expertise.id'
                )
            )
        )
    else:
        query = query | ConstantScore(boost=0.5, filter=MatchAll())

    location = user.location or user.place
    if location and location.position:
        query = query | ConstantScore(
            filter=Q(
                'geo_distance',
                distance='50000m',
                position={
                    'lat': location.position.y,
                    'lon': location.position.x
                },
            )
        )

    result = search.query(
        FunctionScore(
            score_mode='sum',
            query=query
        )
    ).extra(explain=True).execute()

    matched = [activity for activity in result if activity.meta.score > 2]
    activities = list(
        Activity.objects.filter(
            pk__in=[int(match.meta.id) for match in matched],
        ).exclude(contributors__user=user)
    )

    if len(activities) < 3:
        partially_matched = [activity for activity in result if activity.meta.score == 2]
        activities += list(
            Activity.objects.filter(
                pk__in=[int(match.meta.id) for match in partially_matched],
            ).exclude(contributors__user=user)
        )

    return activities


@periodic_task(
    run_every=(crontab(0, 0, day_of_month='2')),
    name="recommend",
    ignore_result=True
)
def recommend():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            settings = InitiativePlatformSettings.objects.get()
            if settings.enable_matching_emails:
                for user in Member.objects.filter(subscribed=True):
                    activities = get_matching_activities(user)

                    if activities:
                        notification = MatchingActivitiesNotification(user)
                        try:
                            notification.compose_and_send(
                                activities=activities
                            )
                        except Exception as e:
                            logger.error(e)


@periodic_task(
    run_every=(crontab(minute=0, hour=10)),
    name="do_good_hours_reminder",
    ignore_result=True
)
def do_good_hours_reminder():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            settings = MemberPlatformSettings.objects.get()
            if settings.do_good_hours:
                offset = settings.fiscal_month_offset
                today = date.today()
                q1 = (datetime(2000, 1, 1).date() + relativedelta(months=offset)).replace(today.year)
                q2 = q1 + relativedelta(months=3)
                q3 = q1 + relativedelta(months=6)
                q4 = q1 + relativedelta(months=9)
                notification = None
                if settings.reminder_q1 and today == q1:
                    notification = DoGoodHoursReminderQ1Notification(settings)
                if settings.reminder_q2 and today == q2:
                    notification = DoGoodHoursReminderQ2Notification(settings)
                if settings.reminder_q3 and today == q3:
                    notification = DoGoodHoursReminderQ3Notification(settings)
                if settings.reminder_q4 and today == q4:
                    notification = DoGoodHoursReminderQ4Notification(settings)

                if notification:
                    try:
                        notification.compose_and_send()
                    except Exception as e:
                        logger.error(e)


@periodic_task(
    run_every=(crontab(minute=0, hour=10)),
    name="data_retention_contributions",
    ignore_result=True
)
def data_retention_contribution_task():
    for tenant in Client.objects.filter(client_name='onepercent').all():
        with LocalTenant(tenant, clear_tenant=True):
            settings = MemberPlatformSettings.objects.get()
            if settings.retention_anonymize:
                history = now() - relativedelta(months=settings.retention_anonymize)
                contributors = Contributor.objects.filter(created__lt=history, user__isnull=False)
                if contributors.count():
                    logger.info(f'DATA RETENTION: {tenant.schema_name} anonymizing {contributors.count} contributors')
                    contributors.update(
                        user=None,
                    )
            if settings.retention_delete:
                history = now() - relativedelta(months=settings.retention_delete)
                contributors = Contributor.objects.filter(created__lt=history, user__isnull=False)
                if contributors.count():
                    logger.info(f'DATA RETENTION: {tenant.schema_name} deleting {contributors.count} contributors')
                    # TODO: Delete contributors + add successful count to activity
