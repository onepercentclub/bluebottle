from django.contrib.contenttypes.admin import GenericTabularInline
from bluebottle.follow.models import Follow


class FollowAdminInline(GenericTabularInline):
    model = Follow
    ct_fk_field = "instance_id"
    readonly_fields = ['created', 'user']
    fields = readonly_fields

    extra = 0
    can_delete = True
