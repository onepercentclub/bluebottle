ACTIVE_CONTRIBUTOR_STATUSES = ('accepted', 'succeeded')


def get_effective_audience(update):
    if update.parent_id:
        return update.parent.audience
    return update.audience


def user_can_view_contributor_updates(user, activity):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if user in activity.owners:
        return True
    return activity.contributors.filter(
        user=user,
        status__in=ACTIVE_CONTRIBUTOR_STATUSES,
    ).exists()


def get_active_contributor_users(activity, exclude=()):
    contributors = activity.contributors.filter(
        status__in=ACTIVE_CONTRIBUTOR_STATUSES,
        user__isnull=False,
        user__campaign_notifications=True,
    ).exclude(
        user__in=exclude
    ).select_related('user')
    return list({contributor.user for contributor in contributors})
