#!/usr/bin/env python
# flake8: noqa
import os
import sys
import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


readme = read_file('README.rst')
changes = ''

install_requires = [
    'Babel==2.4.0',
    'Django==2.0.13',
    'Pillow==7.2.0' if sys.version_info.major == 3 else 'Pillow==6.2.2',
    'South==1.0.2',
    'beautifulsoup4==4.6.0',
    'bleach==3.3.0',
    'clamd==1.0.2',
    'celery==4.3',
    'dotted==0.1.8',
    'defusedxml==0.6.0',
    'django-admin-sortable==2.2.1',
    'django-admin-tools==0.8.1',
    'django-adminfilters==1.4.1',
    'django-appconf==1.0.3',
    'django-axes==4.5.4',
    'django-choices==1.5.0',
    'django-cors-headers==3.7.0',
    'django-daterange-filter==1.3.0',
    'django-dynamic-fixture==1.9.5',
    'django-elasticsearch-dsl==0.5.0',
    'django-filter==2.3.0',
    'django-geoposition==0.3.0',
    'django-fluent-contents==2.0.7',
    'django-fluent-dashboard==1.0a1',
    'django-fsm==2.5.0',
    'django-hashers-passlib==0.3',
    'django-ipware==2.1.0',
    'django-jet2==1.0.12',
    'django-localflavor==3.0.1',
    'django-lockdown==1.4.2',
    'django-loginas==0.3.2',
    'django-map-widgets==0.3.1',
    'django-memoize==2.3.1',
    'django-modeltranslation==0.12.1',
    'django-money==0.15.1',
    'django-parler==2.1',
    'django-permissions-widget==1.5.2',
    'django_polymorphic==2.1.2',
    'django-recaptcha==2.0.6',
    'django-rest-polymorphic==0.1.8',
    'django-rest-swagger==2.1.2',
    'django-singleton-admin-2==1.1.0',
    'django-subquery==1.0.4',
    'django-summernote==0.8.11.6',
    'django-taggit==0.22.1',
    'django-tenant-schemas==1.9.0',
    'django-tinymce==2.7.0',
    'django-tools==0.48.3',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.8.0',
    'djangorestframework-jsonapi==2.8.0',
    'drf-jwt==1.19.0',
    'djangorestframework==3.8.2',
    'dkimpy==1.0.5',
    'elasticsearch==6.3.0',
    'elasticsearch-dsl==6.1.0',
    'geocoder==1.37.0',
    'gunicorn==19.7.1',
    'html5lib==1.0b10',
    'icalendar==4.0.4',
    'influxdb==4.1.1',
    'lipisha==0.2.4',
    'lxml==4.3.0',
    'micawber==0.5.2',
    'mixpanel==4.3.2',
    'munch==2.5.0',
    'django-multiselectfield==0.1.12',
    'openpyxl==2.4.8',
    'pendulum==1.2.4',
    'psycopg2-binary==2.8.6',
    'py-moneyed==0.8',
    'pyasn1==0.4.2',
    'pygeoip==0.3.2',
    'pyjwt==2.0.1',
    'python-dateutil==2.6.1',
    'python-magic==0.4.15',
    'python-memcached==1.58',
    'python3-saml==1.9.0' if sys.version_info.major == 3 else 'python-saml==2.1.7',
    'python-social-auth==0.3.6',
    'social-auth-app-django==4.0.0',
    'surlex==0.2.0',
    'rave-python==1.0.2',
    'raven==6.1.0',
    'regex==2017.05.26',
    'requests==2.24.0',
    'schwifty==2.1.0',
    'sorl-thumbnail==12.6.3',
    'South==1.0.2',
    'Sphinx==1.6.3',
    'staticmaps-signature==0.2.0',
    'stripe==2.33.0',
    'suds-jurko==0.6',
    'SurveyGizmo==1.2.2',
    'tablib==0.14.0',
    'timezonefinder==3.4.2',
    'unicodecsv==0.14.1',
    'wheel==0.29.0',
    'xlrd==1.2.0',
    'xlsxwriter==0.9.8',

    # Github requirements
    'django-exportdb @ git+https://github.com/onepercentclub/django-exportdb.git@0.4.8#egg=django-exportdb-0.4.8-github',
    'django-tenant-extras @ git+https://github.com/onepercentclub/django-tenant-extras.git@2.0.15#egg=django-tenant-extras-2.0.15',
    'django-taggit-autocomplete-modified @ git+https://github.com/onepercentclub/django-taggit-autocomplete-modified.git@8e7fbc2deae2f1fbb31b574bc8819d9ae7c644d6#egg=django-taggit-autocomplete-modified-0.1.1b1',
]

tests_requires = [
    'coverage==4.4.1',
    'coveralls==1.1',
    'django-nose==1.4.4',
    'django-setuptest==0.2.1',
    'django-slowtests==0.5.1',
    'django-webtest==1.9.2',
    'factory-boy==2.12.0',
    'httmock==1.2.6',
    'mock==4.0.2' if sys.version_info.major == 3 else 'mock==3.0.5',
    'nose==1.3.7',
    'pylint==1.7.2',
    'pyquery==1.2.17',
    'pylint-django==0.7.2',
    'tblib==1.3.2',
    'tdaemon==0.1.1',
    'WebTest==2.0.27',
    'sniffer==0.4.0',
    'vine==1.3.0'
]

dev_requires = [
    'ipdb',
    'flake8'
]

setup(
    name='bluebottle',
    version=bluebottle.__version__,
    license='BSD',

    # Packaging.
    packages=find_packages(exclude=('tests', 'tests.*')),
    install_requires=install_requires,

    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': dev_requires,
        'test': tests_requires,
    },
    include_package_data=True,
    zip_safe=False,

    # Metadata for PyPI.
    description='Bluebottle, the crowdsourcing framework initiated by the 1%Club.',
    long_description='\n\n'.join([readme, changes]),
    author='1%Club',
    author_email='info@onepercentclub.com',
    platforms=['any'],
    url='https://github.com/onepercentclub/bluebottle',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ]
)
