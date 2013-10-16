from django.core.exceptions import FieldError
from django.template.defaultfilters import truncatechars


from rest_framework import serializers
from taggit.managers import _TaggableManager


from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.bluebottle_utils.validators import validate_postal_code
from bluebottle.bluebottle_utils.models import Address


class AddressSerializer(serializers.ModelSerializer):

    def validate_postal_code(self, attrs, source):
        value = attrs[source]
        if value:
            country_code = ''
            if 'country' in attrs:
                country_code = attrs['country']
            elif self.object and self.object.country:
                country_code = self.object.country.alpha2_code

            if country_code:
                validate_postal_code(value, country_code)
        return attrs

    class Meta:
        model = Address
        fields = ('id', 'line1', 'line2', 'city', 'state', 'country', 'postal_code')



class MetaModelSerializer(serializers.ModelSerializer):
    """ Serializer which fills meta data based on model attributes """

    # Set to None to disable
    page_title_field_name = 'title'
    page_description_field_name = 'description'
    page_keywords_field_name = 'tags'
    page_image_source = None

    def __init__(self, *args, **kwargs):
        """ Call the default __init__ and then add fields with meta-data """
        super(MetaModelSerializer, self).__init__(*args, **kwargs)

        # if the field names don't collide, add the fields
        if not self.fields.get('page_title', None):
            self.fields['page_title'] = serializers.SerializerMethodField('get_page_title')

        if not self.fields.get('page_description', None):
            self.fields['page_description'] = serializers.SerializerMethodField('get_page_description')

        if not self.fields.get('page_keywords', None):
            self.fields['page_keywords'] = serializers.SerializerMethodField('get_page_keywords')

        if self.page_image_source is not None and not self.fields.get('page_image', None):
            self.fields['page_image'] = ImageSerializer(
                                            required = False, read_only = True, 
                                            source = self.page_image_source
                                        )

    def _get_field(self, obj, field_name):
        """ Allow traversing the relations tree for fields """
        attrs = field_name.split('__')
        
        field = obj
        for attr in attrs:
            try:
                field = getattr(field, attr)
            except AttributeError:
                raise FieldError('Unknown field "%s" in "%s"' % (attr, field_name))
        return field

    def get_page_title(self, obj):
        """ Get the page title based on a model attribute """
        if self.page_title_field_name is not None:
            title = self._get_field(obj, self.page_title_field_name)
            return title
        return ''

    def get_page_description(self, obj):
        """ Get the page description based on a model attribute """
        if self.page_description_field_name is not None:
            desc = self._get_field(obj, self.page_description_field_name)
            return truncatechars(desc, 150)
        return ''

    def get_page_keywords(self, obj):
        if self.page_keywords_field_name is not None:
            field = self._get_field(obj, self.page_keywords_field_name)

            # we're dealing with taggit.Tag's here
            if isinstance(field, _TaggableManager):
                keywords = [tag.name.lower() for tag in field.all()]
            else:
                # try to split the keywords
                try:
                    keywords = field.lower().split()
                except AttributeError:
                    keywords = ''
            
            return ", ".join(keywords)
        return ''
