import os

import geocoder
from django.contrib.gis.geos import Point

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation, Place


def geocode(address):
    result = geocoder.google(address, maxRows=1)
    print("Looking up address {}".format(address))
    if result:
        coords = result[0].latlng
        print("Found {}".format(coords))
        return Point(coords[1], coords[0])
    return None


def run(*args):
    import json
    with open('geocoding.json') as json_file:
        lookup = json.load(json_file)

    if not os.environ.get('GOOGLE_API_KEY'):
        print("export GOOGLE_API_KEY xxx")
        print("Look up secret at https://console.cloud.google.com/apis/credentials")
    tne = Client.objects.get(schema_name='nlcares')

    with LocalTenant(tne):
        total = Geolocation.objects.filter(position__isnull=True).count()
        count = 0
        print("Geocoding activity locations")
        for loc in Geolocation.objects.filter(position__isnull=True).all():
            count += 1
            print("{} / {}".format(count, total))
            if loc.street in ['thuis!', 'Thuis!']:
                address = "Amsterdam, Nederland"
            else:
                address = "{}, {}, Nederland".format(loc.street, loc.locality)
            try:
                position = Point(lookup[address])
            except KeyError:
                position = geocode(address)
                if position:
                    lookup[address] = position.coords
            if position:
                loc.position = position
                loc.save()
            else:
                print("Could not find a location for {}".format(address))
                print("geolocation {}".format(loc.id))
        total = Place.objects.filter(position__isnull=True).count()

        print('Write geocoding file')
        with open('geocoding.json', 'w') as outfile:
            json.dump(lookup, outfile, indent=4)

        print("Geocoding user locations")
        count = 0
        # for loc in Place.objects.filter(position__isnull=True).all():
        #     count += 1
        #     print("{} / {}".format(count, total))
        #     address = "{}, {}, Nederland".format(loc.street, loc.locality)
        #     loc.position = geocode(address)
        #     loc.save()
