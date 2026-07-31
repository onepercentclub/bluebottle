from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect, AutocompleteSelectMultiple


class SegmentTypeAutocompleteMixin:
    def __init__(self, field, segment_type_id, admin_site=None, attrs=None):
        self.segment_type_id = segment_type_id
        super().__init__(field, admin_site or admin.site, attrs=attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        url = attrs['data-ajax--url']
        separator = '&' if '?' in url else '?'
        attrs['data-ajax--url'] = f'{url}{separator}segment_type={self.segment_type_id}'
        return attrs


class SegmentAutocompleteSelectMultiple(SegmentTypeAutocompleteMixin, AutocompleteSelectMultiple):
    pass


class SegmentAutocompleteSelect(SegmentTypeAutocompleteMixin, AutocompleteSelect):
    pass
