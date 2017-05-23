from datetime import date
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.suggestions.models import Suggestion


class ExpiredFilter(admin.SimpleListFilter):
    title = _('expired')

    parameter_name = 'isexpired'
    default_expired = 'notexpired'

    def lookups(self, request, model_admin):
        return (
            ('notexpired', _("Not Expired")),
            ('expired', _("Expired")),
            ('all', _("All"))
        )

    def queryset(self, request, queryset):

        if self.value() == 'expired':
            return queryset.filter(deadline__lt=date.today())

        if self.value() == 'notexpired' or not self.value():
            return queryset.filter(deadline__gte=date.today())

        if self.value() == 'all':
            return queryset

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_expired,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }


class SuggestionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'destination', 'deadline', 'created', 'updated', 'status')
    list_filter = ('status', 'destination', ExpiredFilter)

    readonly_fields = ('created', 'updated', 'expired')

    def updated(self, obj):
        return obj.updated

    def created(self, obj):
        return obj.created

    def expired(self, obj):
        return obj.expired

    raw_id_fields = ('project',)

    readonly_fields = ('project_link',)

    def project_link(self, obj):
        if obj.project:
            url = reverse(
                'admin:{0}_{1}_change'.format(obj.project._meta.app_label,
                                              obj.project._meta.model_name),
                args=[obj.project.id]
            )
            return format_html(
                u"<a href='{}' target='_blank'>{}</a>",
                url,
                obj.project.title
            )
        return u"(None)"

    project_link.short_description = _('Project link')


from django.contrib.admin.sites import AlreadyRegistered

try:
    admin.site.register(Suggestion, SuggestionAdmin)
except AlreadyRegistered:  # happens in testing
    pass
