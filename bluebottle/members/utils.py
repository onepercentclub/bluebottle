from builtins import str
from bluebottle.clients import properties


def get_jwt_secret(user):
    return properties.SECRET_KEY + (str(user.last_logout) if user.last_logout else '')
