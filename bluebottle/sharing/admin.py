from django.contrib import admin, messages
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from bluebottle.sharing.models import PlatformConnection, SharedActivity


@admin.register(PlatformConnection)
class PlatformConnectionAdmin(admin.ModelAdmin):
    list_display = ['platform']


@admin.register(SharedActivity)
class SharedActivityAdmin(admin.ModelAdmin):
    readonly_fields = ['title', 'remote_id', 'platform', 'created', 'accept', 'activity', 'data']

    list_display = ['title', 'platform']

    def accept(self, obj):
        if obj and not obj.activity:
            url = reverse('admin:sharedactivity_accept', args=((obj.id),))
            return format_html(f'<a href="{url}">Accept</a>')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/accept/',
                self.admin_site.admin_view(self.accept_activity),
                name='sharedactivity_accept',
            ),
        ]
        return custom_urls + urls

    def accept_activity(self, request, pk):
        activity = get_object_or_404(SharedActivity, pk=pk)
        try:
            activity.accept()  # Call the accept method on the model
            self.message_user(request, f"Accepted activity: {activity.title}", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error accepting activity: {str(e)}", messages.ERROR)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['accept_url'] = f"{object_id}/accept/"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
