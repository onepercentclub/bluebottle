from builtins import object

from adminsortable.admin import NonSortableParentAdmin, SortableTabularInline
from django.contrib import admin
from django.urls import reverse
from django.utils import translation
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from parler.admin import SortedRelatedFieldListFilter, TranslatableAdmin
from polymorphic.admin import PolymorphicInlineSupportMixin

from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.geo.models import Country
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings, Theme, ActivitySearchFilter, \
    InitiativeSearchFilter
from bluebottle.notifications.admin import MessageAdminInline, NotificationAdminMixin
from bluebottle.utils.admin import BasePlatformSettingsAdmin, export_as_csv_action, TranslatableAdminOrderingMixin
from bluebottle.wallposts.admin import WallpostInline


class InitiativeAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Initiative
        fields = '__all__'
        widgets = {
            'story': SummernoteWidget(attrs={'height': 400})
        }


class InitiativeReviewerFilter(admin.SimpleListFilter):
    title = _('Reviewer')
    parameter_name = 'reviewer'

    def lookups(self, request, model_admin):
        reviewers = Initiative.objects.filter(reviewer__isnull=False). \
            distinct('reviewer__id', 'reviewer__first_name', 'reviewer__last_name'). \
            values_list('reviewer__id', 'reviewer__first_name', 'reviewer__last_name'). \
            order_by('reviewer__first_name', 'reviewer__last_name', 'reviewer__id')
        return [('me', _('My initiatives'))] + [(r[0], u"{} {}".format(r[1], r[2])) for r in reviewers]

    def queryset(self, request, queryset):
        if self.value() == 'me':
            return queryset.filter(
                reviewer=request.user
            )
        elif self.value():
            return queryset.filter(
                reviewer__id=self.value()
            )
        else:
            return queryset


class InitiativeCountryFilter(admin.SimpleListFilter):
    title = _("Country")
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        language = translation.get_language()
        country_ids = Initiative.objects. \
            filter(place__isnull=False).distinct('place__country'). \
            values_list('place__country__id', flat=True)
        countries = Country.objects.filter(id__in=country_ids).language(language). \
            order_by('translations__name')
        return [(c.id, c.name) for c in countries]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(place__country_id=self.value())
        return queryset


class ActivityManagersInline(admin.TabularInline):
    model = Initiative.activity_managers.through
    show_change_link = True
    extra = 0

    def user_link(self, obj, field):
        user = obj.member

        url = reverse(
            'admin:{0}_{1}_change'.format(
                user._meta.app_label,
                user._meta.model_name
            ),
            args=[obj.id]
        )
        return format_html(u"<a href='{}'>{}</a>", str(url), getattr(user, field))

    def full_name(self, obj):
        return self.user_link(obj, 'full_name')

    def email(self, obj):
        return self.user_link(obj, 'email')

    readonly_fields = ('full_name', 'email',)
    exclude = ('member',)


@admin.register(Initiative)
class InitiativeAdmin(PolymorphicInlineSupportMixin, NotificationAdminMixin, StateMachineAdmin):
    form = InitiativeAdminForm

    prepopulated_fields = {"slug": ("title",)}

    raw_id_fields = (
        'owner', 'reviewer',
        'promoter',
        'organization', 'organization_contact',
        'place',
        'theme',
    )

    date_hierarchy = 'created'
    list_display = ['__str__', 'created', 'owner', 'state_name']

    list_filter = [
        InitiativeReviewerFilter,
        ('categories', SortedRelatedFieldListFilter),
        ('theme', SortedRelatedFieldListFilter),
        StateMachineFilter,
        InitiativeCountryFilter
    ]

    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']

    readonly_fields = ['link', 'created', 'updated', 'has_deleted_data', 'valid']

    ordering = ('-created',)

    export_to_csv_fields = (
        ('title', 'Title'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('pitch', 'Pitch'),
        ('theme', 'Theme'),
        ('image', 'Image'),
        ('video_url', 'Video'),
        ('place', 'Place'),
        ('organization', 'Organization'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Owner email'),
        ('promotor__full_name', 'Promotor'),
        ('promotor__email', 'Promotor email'),
        ('reviewer__full_name', 'Reviewer'),
        ('reviewer__email', 'Reviewer email'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def get_fieldsets(self, request, obj=None):
        detail_fields = [
            'title', 'slug', 'owner',
            'theme', 'categories'
        ]
        detail_fields.append('place')

        if InitiativePlatformSettings.objects.get().enable_open_initiatives:
            detail_fields.append('is_open')

        fieldsets = (
            (_('Details'), {'fields': detail_fields}),
            (_('Description'), {
                'fields': (
                    'pitch', 'story', 'image', 'video_url',
                )
            }),
            (_('Organization'), {
                'fields': (
                    'has_organization', 'organization',
                    'organization_contact'
                )
            }),
            (_('Status'), {'fields': (
                'reviewer', 'activity_managers', 'promoter',
                'valid',
                'status', 'states',
                'created', 'updated', 'has_deleted_data'
            )}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets

    inlines = [
        ActivityAdminInline,
        MessageAdminInline,
        WallpostInline
    ]

    def link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.get_absolute_url, obj.title)

    link.short_description = _("Show on site")

    def valid(self, obj):
        errors = list(obj.errors)
        required = list(obj.required)
        if not errors and not required:
            return '-'

        errors += [
            _("{} is required").format(obj._meta.get_field(field).verbose_name.title())
            for field in required
        ]

        return format_html("<ul class='validation-error-list'>{}</ul>", format_html("".join([
            format_html(u"<li>{}</li>", value) for value in errors
        ])))

    valid.short_description = _('Steps to complete initiative')
    autocomplete_fields = ['activity_managers']


class ActivitySearchFilterInline(SortableTabularInline):
    model = ActivitySearchFilter
    extra = 0

    readonly_fields = ('drag',)
    fields = readonly_fields + ('type', 'highlight')

    def drag(self, obj):
        return format_html('<div style="font-size: 20px">⠿</div>')


class InitiativeSearchFilterInline(SortableTabularInline):
    model = InitiativeSearchFilter
    extra = 0

    readonly_fields = ('drag',)
    fields = readonly_fields + ('type', 'highlight')

    def drag(self, obj):
        return format_html('<div style="font-size: 20px">⠿</div>')


@admin.register(InitiativePlatformSettings)
class InitiativePlatformSettingsAdmin(NonSortableParentAdmin, BasePlatformSettingsAdmin):
    inlines = [ActivitySearchFilterInline, InitiativeSearchFilterInline]

    fieldsets = (
        (_('Activity types'), {
            'fields': (
                'activity_types', 'team_activities',
            )
        }),
        (_('Offices'), {
            'fields': (
                'enable_office_regions', 'enable_office_restrictions',
                'default_office_restriction'
            )
        }),
        (_('Options'), {
            'fields': (
                'contact_method', 'require_organization',
                'enable_impact',
                'enable_open_initiatives', 'enable_participant_exports',
                'enable_matching_emails',
                'include_full_activities'
            )
        }),
    )


@admin.register(Theme)
class ThemeAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('slug', 'disabled', 'initiative_link')
    readonly_fields = ('initiative_link',)
    fields = ('name', 'slug', 'description', 'disabled') + readonly_fields

    def initiative_link(self, obj):
        url = "{}?theme__id__exact={}".format(reverse('admin:initiatives_initiative_changelist'), obj.id)
        return format_html("<a href='{}'>{} initiatives</a>".format(url, obj.initiative_set.count()))

    initiative_link.short_description = _('Initiatives')
