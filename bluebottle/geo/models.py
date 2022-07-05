from builtins import object

import geocoder
from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from parler.models import TranslatedFields
from sorl.thumbnail import ImageField
from timezonefinder import TimezoneFinder

from bluebottle.utils.models import SortableTranslatableModel
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from .validators import Alpha2CodeValidator, Alpha3CodeValidator, \
    NumericCodeValidator

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

    class Meta(GeoBaseModel.Meta):
        ordering = ['translations__name']
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
        verbose_name=_('office group'),
        help_text=_('The organisational group this office belongs too.'),
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    city = models.CharField(_('city'), blank=True, null=True, max_length=255)
    country = models.ForeignKey(
        'geo.Country',
        help_text=_('The (geographic) country this office is located in.'),
        blank=True, null=True,
        on_delete=models.CASCADE
    )
    description = models.TextField(_('description'), blank=True)
    image = ImageField(
        _('image'), max_length=255, null=True, blank=True,
        upload_to='location_images/', help_text=_('Office picture'),
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    class Meta(GeoBaseModel.Meta):
        ordering = ['name']
        verbose_name = _('office')
        verbose_name_plural = _('offices')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(Location, self).save()

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
        return "{0}, {1}".format(self.locality, self.country)


@python_2_unicode_compatible
class Geolocation(models.Model):
    street_number = models.CharField(_('Street Number'), max_length=255, blank=True, null=True)
    street = models.CharField(_('Street'), max_length=255, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    locality = models.CharField(_('Locality'), max_length=255, blank=True, null=True)
    province = models.CharField(_('Province'), max_length=255, blank=True, null=True)
    country = models.ForeignKey('geo.Country', on_delete=models.CASCADE)

    formatted_address = models.CharField(_('Address'), max_length=255, blank=True, null=True)

    position = PointField(null=True)

    anonymized = False

    class JSONAPIMeta(object):
        resource_name = 'geolocations'

    def __str__(self):
        if self.locality:
            return u"{}, {}".format(self.locality, self.country.name)
        else:
            return self.country.name

    @property
    def timezone(self):
        if self.position:
            return tf.timezone_at(
                lng=self.position.x,
                lat=self.position.y
            )
        return 'Europe/Amsterdam'
