from django import forms
from django.contrib import admin
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
        fields = ['event']


class MailAdmin(TranslatableAdmin, SummernoteModelAdmin):

    list_display = ('event', 'recipients_display', 'subject')
    readonly_fields = ('placeholder_display', 'event', 'created', 'updated')

    fieldsets = (
        (_('Main'), {'fields': ['event', ('created', 'updated'), 'recipients', 'subject']}),
        (_('Content'), {'fields': ['body_html', 'placeholder_display', ('action_link', 'action_title')]}),
    )

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else []

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None and obj.related_class is not None:
            kwargs['form'] = mailform_factory(obj)
        else:
            kwargs['form'] = CreateMailAdminForm
        return super(MailAdmin, self).get_form(request, obj, **kwargs)

    def recipients_display(self, obj):
        if len(obj.recipients):
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


admin.site.register(Mail, MailAdmin)
