from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.contenttypes.admin import GenericTabularInline
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from bluebottle.notifications.models import Message, NotificationPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class MessageAdminInline(GenericTabularInline):

    model = Message

    readonly_fields = ['sent', 'subject', 'recipient']
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    extra = 0

    can_delete = False


@admin.register(NotificationPlatformSettings)
class NotificationPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass


class NotificationAdminMixin(object):
    change_confirmation_template = None

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Determines the HttpResponse for the change_view stage.
        """
        obj = self.model.objects.get(pk=object_id)
        new = None
        ModelForm = self.get_form(request, obj)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            new = self.save_form(request, form, change=True)
        old = self.model.objects.get(pk=object_id)

        confirm = request.POST.get('confirm', False)
        send_messages = request.POST.get('send_messages', True)

        notifications = []
        if new and hasattr(self.model, 'get_messages'):
            for message_list in [message(new).get_messages() for message in self.model.get_messages(old, new)]:
                notifications += message_list

        if not new or confirm or not notifications:
            response = super(NotificationAdminMixin, self).changeform_view(request, object_id, form_url, extra_context)
            if confirm and send_messages == 'on':
                for message in notifications:
                    message.send()
            return response

        opts = self.model._meta
        app_label = opts.app_label

        post = request.POST

        title = _("Are you sure?")

        context = dict(
            obj=obj,
            title=title,
            post=post,
            opts=opts,
            media=self.media,
            notifications=notifications
        )

        return TemplateResponse(request, self.change_confirmation_template or [
            "admin/%s/%s/change_confirmation.html" % (app_label, opts.model_name),
            "admin/%s/change_confirmation.html" % app_label,
            "admin/change_confirmation.html",
            "admin/change_confirmation.html"
        ], context)
