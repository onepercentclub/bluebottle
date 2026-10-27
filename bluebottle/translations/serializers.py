from future import standard_library

from bluebottle.members.models import MemberPlatformSettings

standard_library.install_aliases()

from builtins import str

from rest_framework import serializers

from bluebottle.utils.utils import get_api_language
from bluebottle.translations.utils import translate_text_cached
from bluebottle.utils.models import Language


class TranslationsSerializer(serializers.Field):

    def __init__(self, fields=None, **kwargs):
        self.translation_fields = fields or []
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return instance

    def _get_nested_attribute(self, obj, attr_path):
        attrs = attr_path.split('.')
        current = obj

        for attr in attrs:
            current = getattr(current, attr, None)
            if current is None:
                return None

        return current

    def to_representation(self, instance):
        if not instance:
            return {}

        member_settings = MemberPlatformSettings.load()
        if not member_settings.translate_user_content:
            return {}

        target_language = get_api_language() or Language.objects.first().code
        translated_data = {}

        for field in self.translation_fields:
            if isinstance(field, tuple):
                name, field_name = field
            else:
                field_name = name = field

            original_value = self._get_nested_attribute(instance, field_name)

            if hasattr(original_value, 'html'):
                original_value = original_value.html

            text_value = str(original_value)
            translated_value = self._translate_field(
                text_value,
                target_language,
            )
            if translated_value:
                translated_data[name] = translated_value

        return translated_data

    def _translate_field(self, text, target):
        return translate_text_cached(text=text, target_language=target)
