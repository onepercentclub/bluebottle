from urllib.parse import urlparse

from django.db import connection
from django.urls import resolve

from rest_framework import serializers
from rest_framework.reverse import reverse

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.utils import is_local


class RelatedActivityPubField(serializers.Field):
    def __init__(self, serializer_class, *args, **kwargs):
        self.serializer_class = serializer_class
        self.include = kwargs.pop('include', False)

        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        if instance.url is not None:
            url = instance.url
        else:
            url = connection.tenant.build_absolute_url(
                reverse(
                    self.serializer_class().get_url_name(instance),
                    args=[instance.pk],
                )
            )

        if self.include:
            serializer = self.serializer_class()
            serializer.bind(parent=self.parent, field_name=self.field_name)

            representation = serializer.to_representation(instance)
            del representation['type']

            return representation
        else:
            return url

    def to_internal_value(self, data):
        if 'id' in data:
            url = data['id']
        else:
            url = data

        if is_local(url):
            resolved = resolve(urlparse(url).path)
            queryset = resolved.func.cls.queryset

            return queryset.get(**resolved.kwargs)
        else:
            return adapter.sync(url, self.serializer_class)


class IdField(serializers.CharField):
    def to_representation(self, instance):
        if isinstance(instance, dict) and 'url' in instance:
            return instance['url']
        elif instance.url:
            return instance.url
        else:
            return connection.tenant.build_absolute_url(
                reverse(
                    self.parent.get_url_name(instance),
                    args=[instance.pk],
                )
            )

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        if is_local(result):
            return {'id': resolve(urlparse(result).path).kwargs['pk']}
        else:
            return {'id': None}


class TypeValidator:
    requires_context = True

    def __call__(self, value, serialized_field):
        return value == serialized_field.parent.Meta.type


class TypeField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = kwargs.pop('validators', []) + [TypeValidator()]
        kwargs['read_only'] = True
        kwargs['source'] = '*'

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return self.parent.Meta.type
