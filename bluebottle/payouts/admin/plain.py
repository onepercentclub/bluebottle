from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount
from bluebottle.payouts.models.plain import PlainPayoutAccount, PayoutDocument
from bluebottle.projects.forms import UploadWidget


class PayoutDocumentForm(forms.ModelForm):
    class Meta:
        model = PayoutDocument
        widgets = {
            'file': UploadWidget()
        }
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(PayoutDocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False


@admin.register(PayoutDocument)
class PayoutDocumentAdmin(admin.ModelAdmin):
    model = PayoutDocument
    form = PayoutDocumentForm

    raw_id_fields = ('author',)
    readonly_fields = ('download_url', 'created', 'updated', 'ip_address')
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        url = obj.document_url

        if url is not None:
            return format_html(
                u"<a href='{}'>{}</a>",
                str(url), _('Download')
            )
        return '(None)'


@admin.register(PlainPayoutAccount)
class PlainPayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = PlainPayoutAccount
    raw_id_fields = ('user', 'document')
