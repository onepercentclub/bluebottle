from django.contrib import admin

from .models import Follow


class FollowAdmin(admin.ModelAdmin):
    model = Follow
    raw_id_fields = ('user', )
    list_display = ('user', 'content_type', 'title')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'object_id')

    fields = ('user', 'content_type', 'object_id')

    def title(self, obj):
        if obj.followed_object:
            return obj.followed_object.title
        else:
            return '-'


admin.site.register(Follow, FollowAdmin)
