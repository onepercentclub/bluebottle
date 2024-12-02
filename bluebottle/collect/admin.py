from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from parler.admin import TranslatableAdmin

from bluebottle.activities.admin import (
    ActivityChildAdmin, ContributorChildAdmin, ActivityForm, TeamInline, BaseContributorInline
)
from bluebottle.collect.models import CollectContributor, CollectActivity, CollectType, CollectContribution
from bluebottle.utils.admin import export_as_csv_action


class CollectAdminForm(ActivityForm):
    class Meta(object):
        model = CollectActivity
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class CollectContributionInline(admin.TabularInline):
    model = CollectContribution
    extra = 0
    readonly_fields = ('status', 'start',)
    fields = readonly_fields + ('value',)

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CollectContributor)
class CollectContributorAdmin(ContributorChildAdmin):
    readonly_fields = ['created']
    raw_id_fields = ['user', 'activity']
    fields = ['activity', 'user', 'status', 'states'] + readonly_fields
    list_display = ['__str__', 'activity_link', 'status']
    inlines = [CollectContributionInline]


class CollectContributorInline(BaseContributorInline):
    model = CollectContributor


@admin.register(CollectActivity)
class CollectActivityAdmin(ActivityChildAdmin):
    base_model = CollectActivity
    form = CollectAdminForm
    inlines = (TeamInline, CollectContributorInline,) + ActivityChildAdmin.inlines
    list_filter = ['status', 'collect_type']
    search_fields = ['title', 'description']
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']
    readonly_fields = ActivityChildAdmin.readonly_fields + ['team_activity']

    list_display = ActivityChildAdmin.list_display + [
        'start',
        'end',
        'collect_type',
        'contributor_count',
        'target'
    ]

    def contributor_count(self, obj):
        return obj.contributors.count() + obj.deleted_successful_contributors or 0
    contributor_count.short_description = _('Contributors')

    detail_fields = ActivityChildAdmin.detail_fields + (
        'start',
        'end',
    )
    description_fields = ActivityChildAdmin.description_fields + (
        'collect_type',
        'target',
        'realized',
        'location'
    )

    export_as_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('collect_type', 'Type'),
        ('target', 'Target'),
        ('realized', 'Realized'),
        ('start', 'Start'),
        ('end', 'End'),
    )

    actions = [export_as_csv_action(fields=export_as_csv_fields)]


@admin.register(CollectType)
class CollectTypeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('activity_link',)
    readonly_fields = ('activity_link',)
    fields = ('name', 'unit', 'unit_plural', 'disabled', ) + readonly_fields

    def activity_link(self, obj):
        url = "{}?type__id__exact={}".format(reverse('admin:collect_collectactivity_changelist'), obj.id)
        return format_html("<a href='{}'>{} activities</a>".format(url, obj.collectactivity_set.count()))

    activity_link.short_description = _('Activity')
