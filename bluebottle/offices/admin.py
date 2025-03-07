from django.contrib import admin
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import Activity, Contributor, Contribution
from bluebottle.funding.models import Payout
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion
from bluebottle.time_based.models import TeamMember, Slot, Team
from bluebottle.updates.models import Update


class OfficeInline(admin.TabularInline):
    model = Location
    fields = ['link', 'name']
    readonly_fields = ['link']
    extra = 0

    def link(self, obj):
        url = reverse('admin:geo_location_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(OfficeSubRegion)
class OfficeSubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'offices', 'activities')
    model = OfficeSubRegion
    search_fields = ('name', 'description')
    raw_id_fields = ('region',)
    readonly_fields = ('offices', 'activities')
    list_filter = ('region',)

    inlines = [OfficeInline]

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion=obj))
        )

    def activities(self, obj):
        return format_html(
            u'<a href="{}?office_location__subregion__id__exact={}">{}</a>',
            reverse('admin:activities_activity_changelist'),
            obj.id,
            len(Activity.objects.filter(office_location__subregion=obj))
        )

    fields = ('name', 'description', 'region', 'offices', 'activities')


class OfficeSubRegionInline(admin.TabularInline):
    model = OfficeSubRegion
    fields = ['link', 'name']
    readonly_fields = ['link']
    extra = 0

    def link(self, obj):
        url = reverse('admin:offices_officesubregion_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(OfficeRegion)
class OfficeRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'subregions_link', 'offices', 'activities')
    model = OfficeRegion
    search_fields = ('name', 'description')
    readonly_fields = ('offices', 'subregions_link', 'activities')
    inlines = [OfficeSubRegionInline]

    def subregions_link(self, obj):
        return format_html(
            u'<a href="{}?region__id__exact={}">{}</a>',
            reverse('admin:offices_officesubregion_changelist'),
            obj.id,
            len(OfficeSubRegion.objects.filter(region=obj))
        )
    subregions_link.short_description = _('office groups')

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__region__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion__region=obj))
        )

    def activities(self, obj):
        return format_html(
            u'<a href="{}?office_location__subregion__region__id__exact={}">{}</a>',
            reverse('admin:activities_activity_changelist'),
            obj.id,
            len(Activity.objects.filter(office_location__subregion__region=obj))
        )

    fields = ('name', 'description', 'subregions_link', 'offices', 'activities')


def region_manager_filter(queryset, user):

    model = queryset.model
    if user.is_superuser:
        return queryset
    elif user.subregion_manager.count():
        if model == Initiative:
            subregion_filter = Q(activities__office_location__subregion__in=user.subregion_manager.all())
            owner_filter = Q(owner__location__subregion__in=user.subregion_manager.all())
            self_filter = Q(owner=user)
            queryset = queryset.filter(subregion_filter | owner_filter | self_filter).distinct()
        elif issubclass(model, Activity):
            subregion_filter = Q(office_location__subregion__in=user.subregion_manager.all())
            owner_filter = Q(owner__location__subregion__in=user.subregion_manager.all())
            self_filter = Q(owner=user)
            queryset = queryset.filter(subregion_filter | owner_filter | self_filter).distinct()
        elif model == Member:
            subregion_filter = Q(location__subregion__in=user.subregion_manager.all())
            self_filter = Q(id=user.id)
            queryset = queryset.filter(
                subregion_filter | self_filter
            ).distinct()
        elif issubclass(model, Contribution):
            subregion_filter = Q(contributor__activity__office_location__subregion__in=user.subregion_manager.all())
            owner_filter = Q(contributor__activity__owner__location__subregion__in=user.subregion_manager.all())
            self_filter = Q(contributor__activity__owner=user)
            queryset = queryset.filter(subregion_filter | owner_filter | self_filter).distinct()
        elif model == TeamMember:
            subregion_filter = Q(team__activity__office_location__subregion__in=user.subregion_manager.all())
            owner_filter = Q(team__activity__owner__location__subregion__in=user.subregion_manager.all())
            self_filter = Q(team__activity__owner=user)
            queryset = queryset.filter(subregion_filter | owner_filter | self_filter).distinct()
        elif (
            issubclass(model, Contributor)
            or issubclass(model, Slot)
            or model in [Team, Update, Payout]
        ):
            subregion_filter = Q(activity__office_location__subregion__in=user.subregion_manager.all())
            owner_filter = Q(activity__owner__location__subregion__in=user.subregion_manager.all())
            self_filter = Q(activity__owner=user)
            queryset = queryset.filter(subregion_filter | owner_filter | self_filter).distinct()
        else:
            raise NotImplementedError(f'No region manager filter implemented for {model}')
    return queryset


class RegionManagerAdminMixin:

    def get_queryset(self, request):
        queryset = super(RegionManagerAdminMixin, self).get_queryset(request)
        queryset = region_manager_filter(queryset, request.user)
        return queryset
