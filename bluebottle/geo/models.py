from builtins import object

import geocoder
from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from future.utils import python_2_unicode_compatible
from parler.models import TranslatableModel, TranslatedFields
from sorl.thumbnail import ImageField
from timezonefinder import TimezoneFinder

from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from .validators import Alpha2CodeValidator, Alpha3CodeValidator, \
    NumericCodeValidator
from ..utils.models import SortableTranslatableModel

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

    mapbox_id = models.CharField(max_length=500, null=True)

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


@python_2_unicode_compatible
class GeoFeature(TranslatableModel):
    mapbox_id = models.CharField(max_length=5000, unique=True)
    feature_type = models.CharField(max_length=32, blank=True)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=5000, blank=True),
        place_name=models.CharField(_('place_name'), max_length=5000, blank=True)
    )

    class Meta(object):
        verbose_name = _('geo feature')
        verbose_name_plural = _('geo features')

    def __str__(self):
        return self.place_name or self.name or self.mapbox_id


@python_2_unicode_compatible
class Geolocation(models.Model):
    street_number = models.CharField(_('Street Number'), max_length=255, blank=True, null=True)
    street = models.CharField(_('Street'), max_length=255, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    locality = models.CharField(_('Locality'), max_length=255, blank=True, null=True)
    province = models.CharField(_('Province'), max_length=255, blank=True, null=True)
    country = models.ForeignKey('geo.Country', null=True, blank=True, on_delete=models.SET_NULL)
    mapbox_id = models.CharField(max_length=5000, null=True, blank=True)

    formatted_address = models.CharField(_('Address'), max_length=255, blank=True, null=True)

    position = PointField(null=True)

    geofeature = models.ForeignKey(
        'geo.GeoFeature',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='primary_geolocations',
    )

    geofeatures = models.ManyToManyField(
        'geo.GeoFeature', blank=True, related_name='geolocations'
    )

    origin = models.ForeignKey(
        'activity_pub.Place', null=True, related_name="locations", on_delete=models.SET_NULL
    )

    @property
    def activity_pub_url(self):
        return None

    anonymized = False

    class JSONAPIMeta(object):
        resource_name = 'geolocations'

    @property
    def place_name(self):
        if self.geofeature:
            return self.geofeature.place_name
        return self.formatted_address or self.locality or '-'

    def __str__(self):
        geofeature = self.geofeature
        if geofeature:
            place_name = geofeature.safe_translation_getter('place_name', any_language=True)
            if place_name:
                return place_name

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

    def reverse_geocode(self, language=None):
        from bluebottle.geo import mapbox as mapbox_utils

        if not self.position:
            return None

        return mapbox_utils.reverse_geocode_feature(
            self.position.x,
            self.position.y,
            language=language,
        )

    def save(self, *args, **kwargs):
        import requests

        from bluebottle.geo import mapbox as mapbox_utils

        skip_mapbox_sync = kwargs.pop('skip_mapbox_sync', False)
        language = kwargs.pop('mapbox_language', None)
        resolved_feature = kwargs.pop('mapbox_feature', None)

        if not skip_mapbox_sync:
            try:
                if self.position and mapbox_utils.needs_mapbox_id(self.mapbox_id):
                    if resolved_feature is None:
                        resolved_feature = self.reverse_geocode(language=language)
                    if resolved_feature:
                        parsed = mapbox_utils.parse_feature(resolved_feature)
                        mapbox_utils.apply_parsed_feature(self, parsed)

                elif self.mapbox_id and not mapbox_utils.is_v6_mapbox_id(self.mapbox_id):
                    if resolved_feature is None:
                        resolved_feature = mapbox_utils.resolve_geolocation_feature(
                            self, language=language
                        )
                    if resolved_feature:
                        parsed = mapbox_utils.parse_feature(resolved_feature)
                        mapbox_utils.apply_parsed_feature(self, parsed)
            except requests.RequestException:
                pass

        super(Geolocation, self).save(*args, **kwargs)

        if not skip_mapbox_sync and self.mapbox_id and mapbox_utils.is_v6_mapbox_id(self.mapbox_id):
            try:
                if resolved_feature is None:
                    response = mapbox_utils.lookup_by_mapbox_id(
                        self.mapbox_id, language=language
                    )
                    resolved_feature = mapbox_utils._first_feature(response)
                if resolved_feature:
                    mapbox_utils.sync_geofeatures(self, resolved_feature, language=language)
            except requests.RequestException:
                pass
