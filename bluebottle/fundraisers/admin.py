from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils import translation

from babel.numbers import format_currency
from bluebottle.utils.model_dispatcher import get_fundraiser_model

FUNDRAISER_MODEL = get_fundraiser_model()


class FundraiserAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner_link',
                    'amount_donated_override', 'amount_override',
                    'deadline')
    raw_id_fields = ('project', 'owner')

    search_fields = ('title', 'project__title')

    readonly_fields = ('project_link', 'owner_link')

    def amount_override(self, obj):
        return obj.amount

    amount_override.short_description = 'amount asked'

    def amount_donated_override(self, obj):
        return obj.amount_donated

    amount_donated_override.short_description = 'amount donated'

    def project_link(self, obj):
        object = obj.project
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.module_name),
                      args=[object.id])
        return "<a href='{0}'>{1}</a>".format(str(url), object.title)

    project_link.allow_tags = True

    def owner_link(self, obj):
        object = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.module_name),
                      args=[object.id])
        return "<a href='{0}'>{1}</a>".format(
            str(url), object.email)

    owner_link.allow_tags = True
    owner_link.short_description = 'initiator'

admin.site.register(FUNDRAISER_MODEL, FundraiserAdmin)
