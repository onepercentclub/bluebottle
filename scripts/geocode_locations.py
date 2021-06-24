import os

import geocoder
from django.contrib.gis.geos import Point

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation, Place


def geocode(address):
    result = geocoder.google(address, maxRows=1)
    if result:
        coords = result[0].latlng
        return Point(coords[1], coords[0])
    return None


def run(*args):
    if not os.environ.get('GOOGLE_API_KEY'):
        print("export GOOGLE_API_KEY xxx")
        print("Look up secret at https://console.cloud.google.com/apis/credentials")
    tne = Client.objects.get(schema_name='nlcares')
    with LocalTenant(tne):
        for loc in Geolocation.objects.filter(position__isnull=True).all():
            address = "{}, {}, The Netherlands".format(loc.street, loc.locality)
            print("Finding lat long for {}".format(address))
            loc.position = geocode(address)
            loc.save()
        for loc in Place.objects.filter(position__isnull=True).all():
            address = "{}, {}, The Netherlands".format(loc.street, loc.locality)
            loc.position = geocode(address)
            loc.save()
