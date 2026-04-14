from builtins import object

from djchoices import DjangoChoices
from djchoices.choices import ChoiceItem
import geocoder
import requests
from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from future.utils import python_2_unicode_compatible
from parler.models import TranslatedFields
from sorl.thumbnail import ImageField
from timezonefinder import TimezoneFinder

from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from .validators import Alpha2CodeValidator, Alpha3CodeValidator, \
    NumericCodeValidator
from ..utils.models import SortableTranslatableModel

from parler.utils.context import switch_language

tf = TimezoneFinder()


@python_2_unicode_compatible
class GeoBaseModel(SortableTranslatableModel):
    """
    Abstract base model for the UN M.49 geoscheme.
    Refs: http://unstats.un.org/unsd/methods/m49/m49.htm
          http://unstats.un.org/unsd/methods/m49/m49regin.htm
          https://en.wikipedia.org/wiki/United_Nations_geoscheme
          https://en.wikipedia.org/wiki/UN_M.49
    """
    # https://en.wikipedia.org/wiki/ISO_3166-1_numeric
    # http://unstats.un.org/unsd/methods/m49/m49alpha.htm
    numeric_code = models.CharField(_("numeric code"), max_length=3, blank=True,
                                    null=True, unique=True,
                                    validators=[NumericCodeValidator],
                                    help_text=_(
                                        "ISO 3166-1 or M.49 numeric code")
                                    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.numeric_code == '':
            self.numeric_code = None

        super(GeoBaseModel, self).save(*args, **kwargs)

    class Meta(object):
        abstract = True


class Region(GeoBaseModel):
    """
    Macro geographical (continental) region as defined by the UN M.49 geoscheme.
    """
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100)
    )

    class Meta(GeoBaseModel.Meta):
        verbose_name = _("region")
        verbose_name_plural = _("regions")


class SubRegion(GeoBaseModel):
    """
    Geographical sub-region as defined by the UN M.49 geoscheme.
    """
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100)
    )

    region = models.ForeignKey(Region, verbose_name=_("region"), on_delete=models.CASCADE)

    class Meta(GeoBaseModel.Meta):
        verbose_name = _("sub region")
        verbose_name_plural = _("sub regions")


class Country(GeoBaseModel):
    """
    Geopolitical entity (country or territory) as defined by the UN M.49 geoscheme.
    """
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=100)
    )

    subregion = models.ForeignKey(SubRegion, verbose_name=_("sub region"), on_delete=models.CASCADE)
    # https://en.wikipedia.org/wiki/ISO_3166-1
    alpha2_code = models.CharField(_("alpha2 code"), max_length=2, blank=True,
                                   validators=[Alpha2CodeValidator],
                                   help_text=_("ISO 3166-1 alpha-2 code"))
    alpha3_code = models.CharField(_("alpha3 code"), max_length=3, blank=True,
                                   validators=[Alpha3CodeValidator],
                                   help_text=_("ISO 3166-1 alpha-3 code"))
    # http://www.oecd.org/dac/aidstatistics/daclistofodarecipients.htm
    oda_recipient = models.BooleanField(
        _("ODA recipient"), default=False, help_text=_(
            "Whether a country is a recipient of Official Development"
            "Assistance from the OECD's Development Assistance Committee."))

    @property
    def code(self):
        return self.alpha2_code

    @staticmethod
    def get_country_choices():
        return [(country.alpha2_code, country.name) for country in Country.objects.all()]

    class Meta(GeoBaseModel.Meta):
        verbose_name = _("country")
        verbose_name_plural = _("countries")


@python_2_unicode_compatible
class LocationGroup(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    class Meta(GeoBaseModel.Meta):
        ordering = ['name']
        verbose_name = _("location group")
        verbose_name_plural = _("location groups")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Location(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), blank=False, null=True, max_length=255)

    position = PointField(null=True)

    group = models.ForeignKey(
        'geo.LocationGroup',
        verbose_name=_('location group'),
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    subregion = models.ForeignKey(
        'offices.OfficeSubRegion',
        verbose_name=_('work location group'),
        help_text=_('The organisational group this work location belongs too.'),
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    city = models.CharField(_('city'), blank=True, null=True, max_length=255)
    country = models.ForeignKey(
        'geo.Country',
        help_text=_('The (geographic) country this work location is located in.'),
        blank=True, null=True,
        on_delete=models.CASCADE
    )
    description = models.TextField(_('description'), blank=True)
    image = ImageField(
        _('image'), max_length=255, null=True, blank=True,
        upload_to='location_images/', help_text=_('Work location picture'),
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    alternate_names = ArrayField(
        models.CharField(max_length=200), default=list, blank=True
    )

    class Meta(GeoBaseModel.Meta):
        ordering = ['name']
        verbose_name = _('work location')
        verbose_name_plural = _('work locations')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.name not in self.alternate_names:
            self.alternate_names.append(self.name)

        if self.slug not in self.alternate_names:
            self.alternate_names.append(self.slug)

        super(Location, self).save()

    def merge(self, other):
        self.alternate_names += other.alternate_names

        other.member_set.update(location=self)
        other.activity_set.update(office_location=self)

        other.delete()
        self.save()

    class JSONAPIMeta(object):
        resource_name = 'locations'

    def __str__(self):
        return self.name


class Place(models.Model):
    street_number = models.CharField(_('Street Number'), max_length=255, blank=True, null=True)
    street = models.CharField(_('Street'), max_length=255, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    locality = models.CharField(_('Locality'), max_length=255, blank=True, null=True)
    province = models.CharField(_('Province'), max_length=255, blank=True, null=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True, on_delete=models.SET_NULL)

    formatted_address = models.CharField(_('Address'), max_length=255, blank=True, null=True)

    position = PointField(null=True)

    mapbox_id = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        if self.locality and self.country and not self.position:
            result = geocoder.google(
                '{} {}'.format(self.locality, self.country.name),
                key=settings.MAPS_API_KEY

            )
            if result.lat and result.lng:
                self.position = Point(
                    x=float(result.lng),
                    y=float(result.lat)
                )

                self.formatted_address = result.raw['formatted_address']

        super().save(*args, **kwargs)

    @property
    def complete(self):
        return (
            self.street and self.street_number and self.postal_code and self.locality and self.country
        )

    def __str__(self):
        if self.locality and self.country:
            return "{0}, {1}".format(self.locality, self.country)
        return self.locality or self.formatted_address or '-unknown-'


class LevelChoices(DjangoChoices):
    country = ChoiceItem('country', label=_("Country"))
    region = ChoiceItem('region', label=_("Region"))
    postcode = ChoiceItem('postcode', label=_("Postcode"))
    district = ChoiceItem('district', label=_("District"))
    place = ChoiceItem('place', label=_("Place"))
    locality = ChoiceItem('locality', label=_("Locality"))
    neighborhood = ChoiceItem('neighborhou', label=_("Neighborhood"))
    street = ChoiceItem('street', label=_("Street"))
    block = ChoiceItem('block', label=_("Block"))
    address = ChoiceItem('country', label=_("Address"))
    secondary_address = ChoiceItem('country', label=_("Secondary address"))

PLACE_TYPE_ORDER = [
    'country',
    'region',
    'district',
    'place',
    'locality',
    'neighborhood',
    'street',
    'block',
    'postcode',
    'address',
    'secondary_address',
]


class GeoFeature(SortableTranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=512)
    )
    place_type = models.CharField(_('Level'), choices=LevelChoices)
    code = models.CharField(_('Level'), max_length=10, null=True)
    mapbox_id = models.CharField(max_length=100, null=True)



@python_2_unicode_compatible
class Geolocation(models.Model):
    street_number = models.CharField(_('Street Number'), max_length=255, blank=True, null=True)
    street = models.CharField(_('Street'), max_length=255, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    locality = models.CharField(_('Locality'), max_length=255, blank=True, null=True)
    province = models.CharField(_('Province'), max_length=255, blank=True, null=True)
    country = models.ForeignKey('geo.Country', null=True, blank=True, on_delete=models.SET_NULL)
    mapbox_id = models.CharField(max_length=100, null=True, blank=True)

    formatted_address = models.CharField(_('Address'), max_length=255, blank=True, null=True)

    features = models.ManyToManyField(GeoFeature)

    position = PointField(null=True)

    origin = models.ForeignKey(
        'activity_pub.Place', null=True, related_name="locations", on_delete=models.SET_NULL
    )

    @property
    def activity_pub_url(self):
        return None

    anonymized = False

    class JSONAPIMeta(object):
        resource_name = 'geolocations'

    def __str__(self):
        if self.locality and self.country:
            return u"{}, {}".format(self.locality, self.country.name)
        if self.locality:
            return self.locality
        if self.country:
            return self.country.name
        return self.formatted_address or '-unknown-'

    @property
    def timezone(self):
        if self.position:
            return tf.timezone_at(
                lng=self.position.x,
                lat=self.position.y
            )
        return 'Europe/Amsterdam'

    def reverse_geocode(self):
        access_token = settings.MAPBOX_API_KEY
        if not access_token:
            return None

        [lon, lat] = self.position.coords
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json"
        response = requests.get(url, params={'access_token': access_token})

        if response.status_code == 200:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                return data['features'][0]
            else:
                return "No results found."
        else:
            return f"Error: {response.status_code}, {response.text}"

    def update_location(self, replace=False):
        data = self.reverse_geocode()
        if data and data != "No results found.":
            self.mapbox_id = data['id']
            country = None
            if not self.formatted_address or replace:
                self.formatted_address = data['place_name']
            if 'context' in data:
                country = Country.objects.filter(alpha2_code__iexact=data['context'][-1]['short_code']).first()
            elif 'short_code' in data['properties']:
                country = Country.objects.filter(alpha2_code__iexact=data['properties']['short_code']).first()
            if country:
                self.country = country
            else:
                raise ValueError(f"Country not found for {data['context'][-1]['short_code']}")
            if data['place_type'][0] == 'address':
                if not self.street or replace:
                    self.street = data['text']
                if not self.street_number or replace:
                    self.street_number = getattr(data, 'address', '')

            if 'context' in data:
                for context_item in data['context']:
                    if 'place' in context_item['id']:
                        if not self.locality or replace:
                            self.locality = context_item['text']
                    elif 'postcode' in context_item['id']:
                        if not self.postal_code or replace:
                            self.postal_code = context_item['text']
                    elif 'region' in context_item['id']:
                        if not self.province or replce:
                            self.province = context_item['text']

    def migrate(self):
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{self.position.coords[0]},{self.position.coords[1]}.json"
        languages = ['nl', 'de', 'fr', 'en']

        data = requests.get(
            url,
            params={
                'access_token': settings.MAPBOX_API_KEY,
                'permanent': 'true',
                'language': ','.join(languages)
            }
        ).json()

        current_place_type = self.mapbox_id.split('.')[0]
        relevant_place_types = PLACE_TYPE_ORDER[
            :PLACE_TYPE_ORDER.index(current_place_type) + 1
        ]

        for feature in data['features']:
            mapbox_id = feature['properties'].get('mapbox_id')
            place_type = feature['place_type'][0]
            if place_type in relevant_place_types:
                try:
                    geo_feature = GeoFeature.objects.get(mapbox_id=mapbox_id)
                except GeoFeature.DoesNotExist:
                    geo_feature = GeoFeature(
                        mapbox_id=mapbox_id,
                        code=feature['properties'].get('short_code'),
                        place_type=place_type
                    )

                    for language in languages:
                        with switch_language(geo_feature, language):
                            geo_feature.name = feature[f'text_{language}']

                    geo_feature.save()

                self.features.add(geo_feature)

    def save(self, *args, **kwargs):
        self.migrate()
        if self.pk:
            old_instance = Geolocation.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.position != self.position:
                self.update_location(replace=True)
        if self.position and self.mapbox_id in ['unknown', '', None]:
            self.update_location()
        return super().save(*args, **kwargs)
