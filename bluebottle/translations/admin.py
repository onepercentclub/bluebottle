from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from bluebottle.translations.models import Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    readonly_fields = ('truncated_text', 'text', 'source_language', 'target_language')
    list_display = ('truncated_text', 'target_language', 'source_language')

    def truncated_text(self, obj):
        return obj.text[:70]

    truncated_text.admin_order_field = _('Text')

    fields = (
        'text',
        'source_language',
        'translation',
        'target_language',
    )
