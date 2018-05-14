from django.db import models
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from bluebottle.fundraisers.models import Fundraiser
from bluebottle.utils.widgets import SecureAdminURLFieldWidget


class FundraiserAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner_link',
                    'amount_donated_override', 'amount_override',
                    'deadline')
    raw_id_fields = ('project', 'owner')

    search_fields = ('title', 'project__title')

    readonly_fields = ('project_link', 'owner_link')

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def amount_override(self, obj):
        return obj.amount

    amount_override.short_description = 'amount asked'

    def amount_donated_override(self, obj):
        return obj.amount_donated

    amount_donated_override.short_description = 'amount donated'

    def project_link(self, obj):
        object = obj.project
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])

        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            object.title
        )

    def owner_link(self, obj):
        object = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])

        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            object.email
        )

    owner_link.short_description = 'initiator'


admin.site.register(Fundraiser, FundraiserAdmin)
