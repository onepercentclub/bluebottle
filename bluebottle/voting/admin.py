from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin, TranslatableModelForm, TranslatableStackedInline
from parler.forms import TranslatableModelFormMetaclass
from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.cms.models import PollContent
from bluebottle.fsm.admin import StateMachineAdminMixin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm, StateMachineModelFormMetaClass
from bluebottle.translations.admin import TranslatableLabelAdminMixin
from bluebottle.utils.admin import TranslatableAdminOrderingMixin
from bluebottle.voting.models import Poll, PollOption, PollVote


class PollAdminFormMetaClass(StateMachineModelFormMetaClass, TranslatableModelFormMetaclass):
    pass


class PollAdminForm(
    StateMachineModelForm,
    TranslatableModelForm,
    metaclass=PollAdminFormMetaClass,
):
    class Meta:
        model = Poll
        fields = '__all__'


class PollOptionInline(SortableStackedInline, TranslatableStackedInline):
    model = PollOption
    extra = 0
    fields = (
        'title',
        'description',
        'image',
        'video_url',
    )


class PollVoteInline(admin.TabularInline):
    model = PollVote
    extra = 0
    raw_id_fields = ('owner',)
    readonly_fields = ('created', 'updated')
    fields = ('owner', 'option', 'created', 'updated')
    ordering = ('-created',)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'option' and getattr(request, '_poll_obj', None):
            field.queryset = field.queryset.filter(poll=request._poll_obj)
        return field


@admin.register(Poll)
class PollAdmin(
    TranslatableLabelAdminMixin,
    TranslatableAdminOrderingMixin,
    StateMachineAdminMixin,
    TranslatableAdmin,
    AdminImageMixin,
    NonSortableParentAdmin,
):
    model = Poll
    form = PollAdminForm
    inlines = (PollOptionInline, PollVoteInline)
    list_display = ('title', 'end_date', 'state_name', 'vote_count')
    list_filter = (StateMachineFilter, 'end_date')
    search_fields = ('translations__title', 'translations__subtitle')
    translatable_ordering = 'translations__title'
    readonly_fields = ('status', 'pages')
    fields = (
        'title',
        'subtitle',
        'end_date',
        'status',
        'states',
        'pages',
    )
    superadmin_fields = ('force_status',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Details'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets

    def get_formsets_with_inlines(self, request, obj=None):
        request._poll_obj = obj
        return super().get_formsets_with_inlines(request, obj)

    def vote_count(self, obj):
        return obj.votes.count()

    vote_count.short_description = _('votes')

    def pages(self, obj):
        if not obj or not obj.pk:
            return '-'

        links = []
        seen = set()
        blocks = PollContent.objects.filter(poll=obj).select_related(
            'placeholder', 'placeholder__parent_type'
        )
        for block in blocks:
            placeholder = block.placeholder
            if not placeholder or not placeholder.parent_id:
                continue
            key = (placeholder.parent_type_id, placeholder.parent_id)
            if key in seen:
                continue
            seen.add(key)
            parent = placeholder.parent
            if parent is None:
                continue
            url = reverse(
                'admin:{}_{}_change'.format(
                    parent._meta.app_label, parent._meta.model_name
                ),
                args=(parent.pk,),
            )
            links.append(format_html('<a href="{}">{}</a>', url, parent))

        if not links:
            return '-'
        return format_html(
            '<div>{}</div>',
            format_html_join(mark_safe('<br />'), '{}', ((link,) for link in links)),
        )

    pages.short_description = _('Pages')
