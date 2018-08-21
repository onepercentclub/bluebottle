from django.db import models
from django.utils.translation import ugettext_lazy as _
from geoposition.fields import GeopositionField
from sorl.thumbnail import ImageField
from parler.models import TranslatedFields

from bluebottle.utils.models import SortableTranslatableModel
from .validators import Alpha2CodeValidator, Alpha3CodeValidator, \
    NumericCodeValidator


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

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.numeric_code == '':
            self.numeric_code = None

        super(GeoBaseModel, self).save(*args, **kwargs)

    class Meta:
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

    region = models.ForeignKey(Region, verbose_name=_("region"))

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

    subregion = models.ForeignKey(SubRegion, verbose_name=_("sub region"))
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

    class Meta(GeoBaseModel.Meta):
        ordering = ['translations__name']
        verbose_name = _("country")
        verbose_name_plural = _("countries")


class LocationGroup(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    class Meta(GeoBaseModel.Meta):
        ordering = ['name']
        verbose_name = _("location group")
        verbose_name_plural = _("location groups")

    def __unicode__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(_('name'), max_length=255)
    position = GeopositionField(null=True)
    group = models.ForeignKey('geo.LocationGroup', verbose_name=_('location group'),
                              null=True, blank=True)
    city = models.CharField(_('city'), blank=True, null=True, max_length=255)
    country = models.ForeignKey('geo.Country', blank=True, null=True)
    description = models.TextField(_('description'), blank=True)
    image = ImageField(_('image'), max_length=255, null=True, blank=True,
                       upload_to='location_images/', help_text=_('Location picture'))

    class Meta(GeoBaseModel.Meta):
        ordering = ['name']
        verbose_name = _('location')
        verbose_name_plural = _('locations')

    def __unicode__(self):
        return self.name

    @property
    def position_tuple(self):
        return (self.position.longitude, self.position.latitude)
