from elasticsearch.exceptions import ElasticsearchException
from elasticsearch_dsl import Q as ESQ

from bluebottle.activities.documents import activity


def is_activity_manager(user):
    return activity.search().filter(ESQ('term', manager=user.pk)).count() > 0


def is_platform_manager(user):
    return user.has_perm('activities.api_review_activity')


def audiences(user):
    result = set()
    if is_activity_manager(user):
        result.add('manager')
    if is_platform_manager(user):
        result.add('platform_manager')
    return result


def has_actions(user):
    if is_platform_manager(user):
        return True

    try:
        return is_activity_manager(user)
    except ElasticsearchException:
        return False
