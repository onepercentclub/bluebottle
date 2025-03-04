from builtins import object
from django import forms
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.contenttypes.admin import GenericTabularInline
from django.forms import Textarea, TextInput
from django.template.loader import render_to_string
from django.db import router, transaction
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm, TranslatedField

from bluebottle.notifications.models import Message, NotificationPlatformSettings, MessageTemplate
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class MessageAdminInline(GenericTabularInline):
    model = Message

    readonly_fields = ['sent', 'subject', 'recipient']
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
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

        if not object_id:
            with transaction.atomic(using=router.db_for_write(self.model)):
                return self._changeform_view(request, object_id, form_url, extra_context)

        obj = self.get_object(request, object_id)
        new = None
        ModelForm = self.get_form(request, obj)

        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            new = self.save_form(request, form, change=True)
        old = self.get_object(request, object_id)

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


class MessageTemplateAdminCreateForm(forms.ModelForm):
    class Meta(object):
        model = MessageTemplate
        fields = ['message']


class MessageTemplateAdminForm(TranslatableModelForm):
    subject = TranslatedField(widget=TextInput(attrs={'size': 60}))
    body_txt = TranslatedField(widget=Textarea(attrs={'rows': 12, 'cols': 80}))

    class Meta(object):
        model = MessageTemplate
        fields = ['message', 'subject', 'body_html', 'body_txt']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(TranslatableAdmin):
    add_form = MessageTemplateAdminCreateForm
    form = MessageTemplateAdminForm

    readonly_fields = ('placeholders',)

    list_display = ['message']

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return super(MessageTemplateAdmin, self).get_readonly_fields(request, obj=obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(MessageTemplateAdmin, self).get_form(request, obj, **defaults)

    def placeholders(self, obj):
        data = {
            'placeholders': [
                ('{site}', _('URL of the platform')),
                ('{site_name}', _('Name of the platform')),
                ('{first_name}', _('First name of the recipient')),
                ('{contact_email}', _('Contact email of platform'))
            ]
        }
        html = mark_safe(render_to_string("admin/notifications/placeholders.html", data))
        return html
