VERSION = (2, 0, 0, 'beta', 1)


def get_version():
    version = '{}.{}'.format(VERSION[0], VERSION[1])
    if VERSION[2] is not None:
        version = '{}.{}'.format(version, VERSION[2])
    if VERSION[3] != 'final':
        if VERSION[4] > 0:
            version = '{}{}{}'.format(version, VERSION[3][0], VERSION[4])
        else:
            version = '{}{}'.format(version, VERSION[3][0])
    return version


__version__ = get_version()
