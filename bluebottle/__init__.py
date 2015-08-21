VERSION = (2, 0, 0, 'beta', 1)


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2] is not None:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3] != 'final':
        if VERSION[4] > 0:
            version = '%s%s%s' % (version, VERSION[3][0], VERSION[4])
        else:
            version = '%s%s' % (version, VERSION[3][0])
    return version


__version__ = get_version()
