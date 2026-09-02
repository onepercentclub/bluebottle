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
from bluebottle.voting.models import Poll, PollOption


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
    inlines = (PollOptionInline,)
    list_display = ('title', 'end_date', 'state_name')
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
