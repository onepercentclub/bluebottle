from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from django_singleton_admin.admin import SingletonAdmin
from django_summernote.admin import SummernoteModelAdmin
from django_summernote.widgets import SummernoteWidget
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from bluebottle.mails.models import MailPlatformSettings, Mail


class MailPlatformSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(MailPlatformSettings, MailPlatformSettingsAdmin)


def mailform_factory(obj):

    class MailAdminForm(TranslatableModelForm):
        class Meta:
            widgets = {
                'recipients': forms.CheckboxSelectMultiple(choices=obj.related_class.roles),
                'body_html': SummernoteWidget()
            }
            model = Mail
            fields = '__all__'

    return MailAdminForm


class CreateMailAdminForm(forms.ModelForm):

    class Meta:
        fields = ('event',)


class MailAdmin(TranslatableAdmin, SummernoteModelAdmin):

    list_display = ('event', 'recipients_display', 'subject')
    readonly_fields = ('placeholder_display', 'event', 'created', 'updated', 'send_test_mail')

    fieldsets = (
        (_('Main'), {'fields': ['event', ('created', 'updated'), 'recipients', 'subject']}),
        (_('Content'), {'fields': ['body_html', 'placeholder_display', ('action_link', 'action_title')]}),
        (_('Test'), {'fields': ['test_object', 'test_email', 'send_test_mail']}),
    )

    def get_urls(self):
        urls = super(MailAdmin, self).get_urls()
        process_urls = [
            url(r'^mail/(?P<pk>\d+)/test$',
                self.process_test_mail,
                name="mails_mail_test"),
        ]
        return process_urls + urls

    def process_test_mail(self, request, queryset):
        # TODO some magic to send a test mail
        pass

    def get_fieldsets(self, request, obj=None):
        if obj:
            return super(MailAdmin, self).get_fieldsets(request, obj)
        return [(None, {'fields': self.get_fields(request, obj)})]

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else []

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None and obj.related_class is not None:
            kwargs['form'] = mailform_factory(obj)
        else:
            kwargs['form'] = CreateMailAdminForm
        return super(MailAdmin, self).get_form(request, obj, **kwargs)

    def recipients_display(self, obj):
        if obj.recipients and len(obj.recipients):
            return ", ".join(eval(obj.recipients))
        return "-"
    recipients_display.short_description = _('Recipients')

    def placeholder_display(self, obj):
        html = '<table>'
        html += '<tr><th>{{ site }}</th><td>Site base url</td></tr>'
        html += '<tr><th>{{ recipient.full_name }}</th><td>Recipient full name</td></tr>'
        html += '<tr><th>{{ recipient.first_name }}</th><td>Recipient first name</td></tr>'
        placeholders = obj.related_class.placeholders
        for k in placeholders:
            html += '<tr><th>{}</th><td>{}</td></tr>'.format(k, placeholders[k])
        html += '</table>'
        return mark_safe(html)

    placeholder_display.short_description = _('Placeholders')

    def send_test_mail(self, obj):
        html = 'Send test email<br/>'
        html += 'Email to {}<br/>'.format(obj.test_email)
        html += '{}<br />'.format(obj.test_model)
        html += '<a href="{}">Send</a>'.format(reverse('admin:mails_mail_test', kwargs={'pk': obj.id}))
        return mark_safe(html)
    send_test_mail.short_description = _('Send test email')


admin.site.register(Mail, MailAdmin)
