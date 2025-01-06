import logging
from datetime import date, datetime

from celery.schedules import crontab
from celery.task import periodic_task
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Case, When
from django.utils.timezone import now
from elasticsearch_dsl.query import (
    Nested, Q, ConstantScore, MatchAll, Term, Terms, GeoDistance
)

from bluebottle.activities.documents import activity
from bluebottle.activities.messages import MatchingActivitiesNotification, DoGoodHoursReminderQ1Notification, \
    DoGoodHoursReminderQ4Notification, DoGoodHoursReminderQ3Notification, DoGoodHoursReminderQ2Notification
from bluebottle.activities.models import Activity, Contributor
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.time_based.models import TeamMember

logger = logging.getLogger('bluebottle')


def get_matching_activities(user):
    settings = InitiativePlatformSettings.objects.get()

    query = ConstantScore(
        filter=Nested(
            path='expertise',
            query=Q('terms', expertise__id=[skill.pk for skill in user.skills.all()])
        )
    ) | ConstantScore(
        boost=1.5,
        filter=Nested(
            path='theme',
            query=Q('terms', theme__id=[theme.pk for theme in user.favourite_themes.all()])
        )
    ) | ConstantScore(boost=0.5, filter=MatchAll())

    search = activity.search().filter(
        Q('terms', status=['open', 'running']) &
        (
            ~Nested(
                path='segments',
                query=(
                    Term(segments__closed=True)
                )
            ) | Nested(
                path='segments',
                query=(
                    Terms(
                        segments__id=[
                            segment.id for segment in user.segments.filter(closed=True)
                        ]
                    )
                )
            )
        ) &
        ~Term(contributors=user.pk)
    )

    if settings.enable_office_restrictions:
        if user.location:
            search = search.filter(
                Nested(
                    path='office_restriction',
                    query=Term(
                        office_restriction__restriction='all'
                    ) | (
                        Term(office_restriction__office=user.location.id) &
                        Term(office_restriction__restriction='office')
                    ) | (
                        Term(
                            office_restriction__subregion=user.location.subregion.id
                            if user.location.subregion else ''
                        ) &
                        Term(office_restriction__restriction='office_subregion')
                    ) | (
                        Term(
                            office_restriction__region=user.location.subregion.region.id
                            if user.location.subregion and user.location.subregion.region else ''
                        ) &
                        Term(office_restriction__restriction='office_region')
                    )
                )
            )
        else:
            search = search.filter(
                Nested(
                    path='office_restriction',
                    query=Term(
                        office_restriction__restriction='all'
                    )
                )
            )

    if user.exclude_online:
        search = search.filter(
            Term(is_online=True)
        )

    if user.search_distance and user.search_distance != "0km" and user.place:
        position = {
            'lat': float(user.place.position[1]),
            'lon': float(user.place.position[0]),
        }
        search = search.filter(
            GeoDistance(distance=user.search_distance, position=position) |
            Term(is_online=True)
        )
        query = query | ConstantScore(
            boost=0.001,
            filter=Q(
                'geo_distance',
                distance=user.search_distance,
                position=position
            )
        )

    result = search.query(query).extra(explain=True).execute()

    pks = [int(match.meta.id) for match in result]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)])

    return Activity.objects.filter(
        pk__in=[int(match.meta.id) for match in result]
    ).order_by(preserved)


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
                    try:
                        activities = get_matching_activities(user)

                        if activities:
                            notification = MatchingActivitiesNotification(user)
                            notification.compose_and_send(activities=activities)
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
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            settings = MemberPlatformSettings.objects.get()
            if settings.retention_anonymize:
                history = now() - relativedelta(months=settings.retention_anonymize)
                Activity.objects.filter(created__lt=history, has_deleted_data=False).update(has_deleted_data=True)
                contributors = Contributor.objects.filter(created__lt=history, user__isnull=False)
                if contributors.count():
                    logger.info(f'DATA RETENTION: {tenant.schema_name} anonymizing {contributors.count()} contributors')
                    contributors.update(
                        user=None,
                    )

                team_members = TeamMember.objects.filter(
                    created__lt=history, user__isnull=False
                )
                if contributors.count():
                    logger.info(
                        f"DATA RETENTION: {tenant.schema_name} anonymizing {team_members.count()} team members"
                    )
                    team_members.update(
                        user=None,
                    )

            if settings.retention_delete:
                history = now() - relativedelta(months=settings.retention_delete)
                contributors = Contributor.objects.filter(created__lt=history)
                if contributors.count():
                    logger.info(f'DATA RETENTION: {tenant.schema_name} deleting {contributors.count()} contributors')
                    successful = contributors.filter(contributions__status='succeeded').values('activity_id').\
                        annotate(total=Count('activity_id')).order_by('activity_id')
                    for success in successful:
                        activity = Activity.objects.filter(id=success['activity_id']).get()
                        activity.deleted_successful_contributors = success['total']
                        activity.save(run_triggers=False)
                    for contributor in contributors:
                        contributions = contributor.contributions.all()
                        contributions.update(contributor=None)
                        contributor.delete()

                team_members = TeamMember.objects.filter(created__lt=history)
                if team_members.count():
                    logger.info(
                        f"DATA RETENTION: {tenant.schema_name} deleting {team_members.count()} team members"
                    )
                    team_members.delete()
