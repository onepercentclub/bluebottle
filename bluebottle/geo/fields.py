import six
from django.contrib.gis.forms import PointField as GisPointField
from django.contrib.gis.geos import Point
from django.utils.encoding import smart_text
from geoposition import Geoposition
from geoposition.fields import GeopositionField
from mapwidgets import GooglePointFieldWidget


class LatLngPoint(Point):

    @property
    def latitude(self):
        return self.coords[1]

    @property
    def longitude(self):
        return self.coords[0]


class PointWidget(GooglePointFieldWidget):

    def serialize(self, value):
        if hasattr(value, 'coords'):
            coords = value.coords
            value = [coords[1], coords[0]]
        return value

    def deserialize(self, value):
        return super(PointWidget, self).deserialize(value)

    def render(self, name, value, attrs=None, renderer=None):
        if value and isinstance(value, six.string_types):
            value = self.deserialize(value)
        if isinstance(value, Geoposition):
            value = Point(float(value.longitude), float(value.latitude))
        return super(PointWidget, self).render(name, value, attrs, renderer)


class PointFormField(GisPointField):

    widget = PointWidget


class PointField(GeopositionField):

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return smart_text(value)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': PointFormField
        }
        defaults.update(kwargs)
        return super(GeopositionField, self).formfield(**defaults)

    def get_prep_value(self, value):
        if not value:
            return None
        return "{},{}".format(value.coords[1], value.coords[0])

    def to_python(self, value):
        if not value or value == 'None':
            return None
        if isinstance(value, Point):
            return value

        value_parts = value.rsplit(',')
        try:
            latitude = value_parts[0]
        except IndexError:
            latitude = '0.0'
        try:
            longitude = value_parts[1]
        except IndexError:
            longitude = '0.0'

        if not isinstance(longitude, float):
            longitude = float(longitude)
            latitude = float(latitude)

        return LatLngPoint(longitude, latitude)
