import json

import logging
from faker import Faker


# Suppress debug information for Factory Boy
logging.getLogger('factory').setLevel(logging.WARN)


fake = Faker()


def generate_rich_text():

    return json.dumps({'html': fake.text(), 'delta': ''})
