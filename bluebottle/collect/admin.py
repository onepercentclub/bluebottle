from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from parler.admin import TranslatableAdmin

from bluebottle.activities.admin import (
    ActivityChildAdmin, ContributorChildAdmin, ActivityForm, TeamInline
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


@admin.register(CollectContributor)
class CollectContributorAdmin(ContributorChildAdmin):
    readonly_fields = ['created']
    raw_id_fields = ['user', 'activity']
    fields = ['activity', 'user', 'status', 'states'] + readonly_fields
    list_display = ['__str__', 'activity_link', 'status']
    inlines = [CollectContributionInline]


class CollectContributorInline(admin.TabularInline):
    model = CollectContributor
    raw_id_fields = ['user']
    readonly_fields = ['edit', 'created', 'transition_date', 'contributor_date', 'status']
    fields = ['edit', 'user', 'created', 'status']
    extra = 0

    template = 'admin/participant_list.html'

    def edit(self, obj):
        if not obj.user and obj.activity.has_deleted_data:
            return format_html(f'<i>{_("Anonymous")}</i>')
        url = reverse('admin:collect_collectcontributor_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, _('Edit contributor'))
    edit.short_description = _('Edit contributor')

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if obj.has_deleted_data:
            fields += ('user',)
        return fields


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
        'enable_impact',
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
