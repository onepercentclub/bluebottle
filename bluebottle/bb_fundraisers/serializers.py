from django.utils.translation import ugettext as _
from rest_framework import serializers

from bluebottle.utils.model_dispatcher import get_fundraiser_model
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import EuroField, ImageSerializer, OEmbedField
from bluebottle.utils.serializers import MetaField


FUNDRAISER_MODEL = get_fundraiser_model()


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

        if request.method == 'PUT' and field_name not in data and not files:
            return 

        return super(ImageSerializerExt, self).field_from_native(data, files, field_name, into)


class BaseFundraiserSerializer(serializers.ModelSerializer):
    """ Serializer to view/create fundraisers """

    owner = UserPreviewSerializer(read_only=True)
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    image = ImageSerializerExt()
    amount_donated = serializers.DecimalField(source='amount_donated', read_only=True)
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

    def validate_deadline(self, attrs, source):
        """ Field level validation for deadline field, see http://www.django-rest-framework.org/api-guide/serializers#validation"""
        if not attrs.get('deadline', None) or not attrs.get('project', None) or attrs.get('deadline') > attrs.get('project').deadline:
            raise serializers.ValidationError(_("Fundraiser deadline exceeds project deadline."))
        return attrs
