from fluent_contents.rendering import render_placeholder
from django.utils.safestring import mark_safe

from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import SorlImageField
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.utils.serializers import MetaField

from .models import NewsItem


class NewsItemContentsField(serializers.Field):
    def to_native(self, obj):
        request = self.context.get('request', None)
        contents_html = mark_safe(render_placeholder(request, obj).html)
        return contents_html


class NewsItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')
    body = NewsItemContentsField(source='contents')
    main_image = SorlImageField('main_image', '300x200', )
    author = get_serializer_class('AUTH_USER_MODEL', 'preview')()

    meta_data = MetaField(
        description='get_meta_description',
        image_source='main_image',
    )

    class Meta:
        model = NewsItem
        fields = ('id', 'title', 'body', 'main_image', 'author',
                  'publication_date', 'allow_comments', 'language', 'meta_data')


class NewsItemPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug')

    class Meta:
        model = NewsItem
        fields = ('id', 'title', 'publication_date')
