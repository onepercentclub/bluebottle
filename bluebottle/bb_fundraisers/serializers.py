from bluebottle.utils.utils import get_model_class
from rest_framework import serializers

from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import EuroField, ImageSerializer, OEmbedField

from bluebottle.utils.serializers import MetaField

FUNDRAISER_MODEL = get_model_class('FUNDRAISERS_FUNDRAISER_MODEL')


class ImageSerializerExt(ImageSerializer):
    """
    Adds semi-logic behaviour for PUT requests (update) to ignore the required flag if the passed URL is identical to
    the existing URL. The PUT-request should actually pass the file object again but this is impractical.
    """
    def field_from_native(self, data, files, field_name, into):
        request = self.context.get('request')

        if request.method == 'PUT' and self.required and field_name in data:
            from django.conf import settings
            from sorl.thumbnail.shortcuts import get_thumbnail

            image_urls = data[field_name]

            existing_value = getattr(self.parent.object, field_name)

            provided_full_url = data[field_name]['full']
            expected_full_url = settings.MEDIA_URL + unicode(get_thumbnail(existing_value, '800x600'))

            if provided_full_url.endswith(expected_full_url):
                return

        return super(ImageSerializerExt, self).field_from_native(data, files, field_name, into)


class FundRaiserSerializer(serializers.ModelSerializer):
    """ Serializer to view/create fundraisers """

    owner = UserPreviewSerializer(read_only=True)
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    image = ImageSerializerExt()
    amount = EuroField()
    amount_donated = EuroField(source='amount_donated', read_only=True)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')

    meta_data = MetaField(
            title = 'get_meta_title', # TODO: specific title format
            image_source = 'image',
            tweet = 'get_tweet',
            )

    class Meta:
        model = FUNDRAISER_MODEL
        fields = ('id', 'owner', 'project', 'title', 'description', 'image','created',
                  'video_html', 'video_url', 'amount', 'amount_donated', 'deadline', 'meta_data')


class FundRaiserPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FUNDRAISER_MODEL
        fields = ('title', 'id')

