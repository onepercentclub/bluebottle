from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from bluebottle.translations.models import Translation
from bluebottle.utils.admin import admin_info_box


class TranslatableLabelAdminMixin:
    """
    Mixin for TranslatableAdmin classes that adds a subtle "Translatable"
    indicator to translatable fields in the Django admin.
    """

    def get_form(self, request, obj=None, **kwargs):
        """
        Mark translatable fields with a CSS class for styling with flag icons.
        """
        form = super().get_form(request, obj, **kwargs)

        # Get the list of translatable field names from the model's translations
        if hasattr(self.model, '_parler_meta'):
            translatable_fields = []
            for field_name in self.model._parler_meta.get_all_fields():
                translatable_fields.append(field_name)

            # Add CSS class to translatable fields for styling
            for field_name in translatable_fields:
                if field_name in form.base_fields:
                    # Add a CSS class to mark this as translatable
                    widget = form.base_fields[field_name].widget
                    if hasattr(widget, 'attrs'):
                        if 'class' in widget.attrs:
                            widget.attrs['class'] += ' translatable-field'
                        else:
                            widget.attrs['class'] = 'translatable-field'
                    else:
                        widget.attrs = {'class': 'translatable-field'}

        return form

    class Media:
        css = {
            'all': ('admin/css/translatable-fields.css',)
        }

    def translatable_info(self, obj):
        return admin_info_box(
            _(
                'Your changes apply to all languages. '
                'Fields marked with the 🌐 icon can be translated separately.'
            ),
            'translatable-info',
        )

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        fields = ('translatable_info',) + tuple(fields)
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        fields = ('translatable_info',) + tuple(fields)
        return fields


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
