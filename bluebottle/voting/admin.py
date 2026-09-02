from adminsortable.admin import NonSortableParentAdmin, SortableStackedInline
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin, TranslatableModelForm, TranslatableStackedInline
from parler.forms import TranslatableModelFormMetaclass
from sorl.thumbnail.admin import AdminImageMixin

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
    readonly_fields = ('vote_count',)
    fields = (
        'title',
        'description',
        'image',
        'video_url',
        'vote_count',
    )

    def vote_count(self, obj):
        if not obj.pk:
            return 0
        return obj.votes.count()

    vote_count.short_description = _('votes')


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
    readonly_fields = ('status',)
    fields = (
        'title',
        'subtitle',
        'end_date',
        'status',
        'states',
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
