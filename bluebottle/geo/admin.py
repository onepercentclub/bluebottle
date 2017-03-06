from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Location, LocationGroup, Region, SubRegion, Country
from bluebottle.projects.models import Project


class LocationFilter(admin.SimpleListFilter):
    title = _('Location')
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        locations = [obj.location for obj in model_admin.model.objects.order_by(
            'location__name').distinct('location__name').exclude(
            location__isnull=True).all()]
        lookups = [(loc.id, loc.name) for loc in locations]

        return lookups

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(location__id__exact=self.value())
        else:
            return queryset


class LocationGroupFilter(admin.SimpleListFilter):
    title = _('location group')
    parameter_name = 'location_group'

    def lookups(self, request, model_admin):
        groups = [obj.location.group for obj in model_admin.model.objects.order_by(
            'location__group__name').distinct('location__group__name').exclude(
            location__group__isnull=True).all()]
        return [(gr.id, gr.name) for gr in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(location__group__id__exact=self.value())
        else:
            return queryset


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_code')


admin.site.register(Region, RegionAdmin)


class SubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_code')
    list_filter = ('region',)


admin.site.register(SubRegion, SubRegionAdmin)


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')
    list_filter = ('oda_recipient', 'subregion__region', 'subregion')
    search_fields = ('name', 'alpha2_code', 'alpha3_code')


admin.site.register(Country, CountryAdmin)


class LocationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
    model = LocationGroup


admin.site.register(LocationGroup, LocationGroupAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'group', 'projects')
    model = Location
    search_fields = ('name', 'description', 'city')

    def projects(self, obj):
        return format_html(
            u'<a href="{}?location={}">{}</a>',
            reverse('admin:projects_project_changelist'),
            obj.id,
            len(Project.objects.filter(location=obj))
        )

    def make_action(self, group):
        name = 'select_%s' % group
        action = lambda modeladmin, req, qset: qset.update(group=group)
        return (name, (action, name, "Move selected to %s" % group))

    def get_actions(self, request):
        return dict([self.make_action(group) for group in LocationGroup.objects.all()])


admin.site.register(Location, LocationAdmin)
