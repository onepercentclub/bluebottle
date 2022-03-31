from rest_framework import filters
from rest_framework.exceptions import ValidationError


class SCIMFilter(filters.SearchFilter):
    field_mapping = {
        'userName': 'remote_id',
        'externalId': 'scim_external_id',
    }

    def filter_queryset(self, request, queryset, view):
        if 'filter' not in request.query_params:
            return queryset

        filter = request.query_params['filter']

        try:
            field, value = filter.split(' eq ')
            mapped_filter = {
                self.field_mapping[field]: value
            }
        except (ValueError, KeyError):
            raise ValidationError(f'Unsupported filter: {filter}')

        return queryset.filter(
            **mapped_filter
        )
