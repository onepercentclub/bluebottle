from bluebottle.clients import properties


def get_jwt_secret(user):
    return properties.SECRET_KEY + (unicode(user.last_logout) if user.last_logout else '')


