MAPBOX_V6_ADDRESS_FEATURE = {
    'type': 'Feature',
    'id': 'dXJuOm1ieGFkcjowYzM5NTBjMi0wMjNhLTQxNTUtOTRmOS1kZTFmZDcxOWQwMTY',
    'geometry': {
        'type': 'Point',
        'coordinates': [3.851166, 51.762731],
    },
    'properties': {
        'mapbox_id': 'dXJuOm1ieGFkcjowYzM5NTBjMi0wMjNhLTQxNTUtOTRmOS1kZTFmZDcxOWQwMTY',
        'feature_type': 'address',
        'name': 'Brouwersdam Buitenzijde 20',
        'full_address': 'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands',
        'context': {
            'address': {
                'mapbox_id': 'dXJuOm1ieGFkcjowYzM5NTBjMi0wMjNhLTQxNTUtOTRmOS1kZTFmZDcxOWQwMTY',
                'address_number': '20',
                'street_name': 'Brouwersdam Buitenzijde',
                'name': 'Brouwersdam Buitenzijde 20',
            },
            'postcode': {
                'mapbox_id': 'dXJuOm1ieHBsYzpwb3N0',
                'name': '3253 MM',
            },
            'place': {
                'mapbox_id': 'dXJuOm1ieHBsYzp4Y2lv',
                'name': 'Ouddorp',
            },
            'region': {
                'mapbox_id': 'dXJuOm1ieHBsYzpaS2c',
                'name': 'South Holland',
                'region_code': 'NL-ZH',
            },
            'country': {
                'mapbox_id': 'dXJuOm1ieHBsYzpJcWc',
                'name': 'Netherlands',
                'country_code': 'NL',
            },
        },
    },
}

MAPBOX_V6_REVERSE_RESPONSE = {
    'type': 'FeatureCollection',
    'features': [MAPBOX_V6_ADDRESS_FEATURE],
}
