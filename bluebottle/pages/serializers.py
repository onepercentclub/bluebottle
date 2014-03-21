from django.template import Context, Template

from fluent_contents.rendering import render_placeholder
from rest_framework import serializers

from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.utils.serializers import MetaField
from .models import Page


class PageContentsField(serializers.Field):

    def to_native(self, obj):
        request = self.context.get('request', None)
        contents_html = render_placeholder(request, obj)
        contents_html = Template(contents_html).render(Context({}))
        return contents_html


class PageSerializer(serializers.ModelSerializer):

    id = serializers.CharField(source='slug', read_only=True)
    body = PageContentsField(source='body')
    author = UserPreviewSerializer()

    meta_data = MetaField(description='get_meta_description', keywords=None)

    class Meta:
        model = Page
        fields = ('title', 'id', 'body', 'language', 'meta_data', 'full_page')
