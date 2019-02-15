from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.initiatives.models import Initiative
from bluebottle.utils.forms import FSMModelForm


class InitiativeAdminForm(FSMModelForm):
    class Meta:
        model = Initiative
        fields = '__all__'


class InitiativeAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', 'reviewer',)
    form = FSMModelForm

    def get_fieldsets(self, request, obj=None):
        return (
            (_('Basic'), {'fields': ('title', 'slug', 'owner', 'image', 'video_url')}),
            (_('Review'), {'fields': ('reviewer', 'review_status', 'review_status_transition')}),
        )

    readonly_fields = ['review_status']


admin.site.register(Initiative, InitiativeAdmin)
