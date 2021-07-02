import json
import os

import geocoder
from django.contrib.gis.geos import Point

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation, Place

with open('geocoding.json') as json_file:
    lookup = json.load(json_file)


def geocode(address):
    result = geocoder.google(address, maxRows=1)
    print("Looking up address {}".format(address))
    if result:
        coords = result[0].latlng
        print("Found {}".format(coords))
        return Point(coords[1], coords[0])
    return None


def find_position(loc):
    if loc.street in ['thuis!', 'Thuis!']:
        address = "Amsterdam, Nederland"
    else:
        address = "{}, {}, Nederland".format(loc.street, loc.locality)
    try:
        position = Point(lookup[address])
    except KeyError:
        position = geocode(address)
    if not position or position.x < 0:
        print("Could not find a location for {}".format(address))
        print("geolocation {}".format(loc.id))
        position = Point([4.9041389, 52.3675734])
    return position


def run(*args):
    if not os.environ.get('GOOGLE_API_KEY'):
        print("export GOOGLE_API_KEY=\"xxx\"")
        print("Look up secret at https://console.cloud.google.com/apis/credentials")
    tenant = Client.objects.get(schema_name='nlcares')

    with LocalTenant(tenant):
        locations = []
        total = Geolocation.objects.filter(position__isnull=True).count()
        count = 0
        print("Geocoding activity locations")
        for loc in Geolocation.objects.filter(position__isnull=True).all():
            count += 1
            print("{} / {}".format(count, total))
            loc.position = find_position(loc)
            if count % 100 == 0:
                print('Write geocoding file an records')
                with open('geocoding.json', 'w') as outfile:
                    json.dump(lookup, outfile, indent=4)
                Geolocation.objects.bulk_update(locations, ['position'])
                locations = []
            locations.append(loc)

        print('Write geocoding file')
        with open('geocoding.json', 'w') as outfile:
            json.dump(lookup, outfile, indent=4)

        places = []
        print("Geocoding user locations")
        total = Place.objects.filter(position__isnull=True).count()
        count = 0
        for loc in Place.objects.filter(position__isnull=True).all():
            count += 1
            if count % 100 == 0:
                print('Write geocoding file and records')
                with open('geocoding.json', 'w') as outfile:
                    json.dump(lookup, outfile, indent=4)
                Place.objects.bulk_update(places, ['position'])
                places = []
            print("{} / {}".format(count, total))
            loc.position = find_position(loc)
            places.append(loc)

        print('Write geocoding file')
        with open('geocoding.json', 'w') as outfile:
            json.dump(lookup, outfile, indent=4)
