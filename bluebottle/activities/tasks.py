import logging

from celery.schedules import crontab
from celery.task import periodic_task

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from elasticsearch_dsl.query import Nested, Q, FunctionScore, ConstantScore, MatchAll

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.activities.documents import activity
from bluebottle.activities.models import Activity
from bluebottle.activities.messages import MatchingActivitiesNotification
from bluebottle.members.models import Member


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
                    'lat': location.position.latitude,
                    'lon': location.position.longitude
                },
            )
        )

    result = search.query(
        FunctionScore(
            score_mode='sum',
            query=query
        )
    ).extra(explain=True).execute()

    matched = [activity for activity in result if activity._score > 2]
    activities = list(
        Activity.objects.filter(
            pk__in=[match._id for match in matched],
        ).exclude(contributors__user=user)
    )

    if len(activities) < 3:
        partially_matched = [activity for activity in result if activity._score == 2]
        activities += list(
            Activity.objects.filter(
                pk__in=[match._id for match in partially_matched],
            ).exclude(contributors__user=user)
        )

    return activities


@periodic_task(
    run_every=(crontab(0, 0, day_of_month='1')),
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
                        notification.compose_and_send(
                            activities=activities
                        )
