#!/usr/bin/env python
# flake8: noqa
import os

import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

readme = read_file('README.rst')
changes = ''

dependency_links = [
    'git+https://github.com/onepercentclub/django-taggit-autocomplete-modified.git@8e7fbc2deae2f1fbb31b574bc8819d9ae7c644d6#egg=django-taggit-autocomplete-modified-0.1.1b1',
    'git+https://github.com/onepercentclub/django-bb-salesforce.git@1.2.2#egg=django-bb-salesforce-1.2.2',
    'git+https://github.com/onepercentclub/django-tenant-extras.git@2.0.14#egg=django-tenant-extras-2.0.14',
    'git+https://github.com/onepercentclub/django-fluent-contents.git@741ffae615a4afed01388a202709ed9a5b60e80f#egg=django-fluent-contents-1.2.1-741ffae6',
    'git+https://github.com/mariocesar/sorl-thumbnail.git@v12.3#egg=sorl-thumbnail-12.3-github',
    'git+https://github.com/onepercentclub/django-token-auth.git@c0bac86a6c3d63f663cd88ca0784c06c73bc8dc0#egg=django-token-auth-0.3.10',
    'git+https://github.com/st4lk/django-select-multiple-field.git@1dc7733008150a111cd141ff7c3f42bf4953dc7d#egg=django-select-multiple-field-0.5.0a-draft',
    'hg+https://bitbucket.org/jdiascarvalho/django-filetransfers@89c8381764da217d72f1fa396ce3929f0762b8f9#egg=django-filetransfers-0.1.1',
    'git+https://github.com/skada/django-money-rates@aeb2edf240471fac64f9cdf71e34f91d632f1b86#egg=django-money-rates-0.3.1-github',
    'git+https://github.com/beyonic/beyonic-python.git#egg=beyonic',
    'git+https://github.com/onepercentclub/flutterwave-python.git@9b6adba8e7eff4204d36ea3a627ebccebe285cf4#egg=Flutterwave-1.1.0'
]

install_requires = [
    'Babel==2.4.0',
    'Django==1.10.8',
    'Pillow==4.1.1',
    'South==1.0.2',
    'beautifulsoup4==4.6.0',
    'bleach==2.1.1',
    'bunch==1.0.1',
    'celery==3.1.24',
    'django-admin-sortable==2.1',
    'django-admin-tools==0.8.1',
    'django-adminfilters==0.3',
    'django-celery==3.2.1',
    'django-choices==1.5.0',
    'django-cors-headers==2.1.0',
    'django-daterange-filter==1.3.0',
    'django-dynamic-fixture==1.9.5',
    'django-extensions==1.7.9',
    'django-exportdb==0.4.7',
    'django-filetransfers==0.1.1',
    'django-filter==1.1.0',
    'django-geoposition==0.3.0',
    'django-fluent-dashboard==1.0a1',
    'django-fsm==2.5.0',
    'django-hashers-passlib==0.3',
    'django-ipware==1.1.6',
    'django-jet==1.0.7',
    'django-localflavor==1.5.2',
    'django-lockdown==1.4.2',
    'django-loginas==0.3.2',
    'django-memoize==2.1.0',
    'django-modeltranslation==0.12.1',
    'django-money==0.11.4',
    'django-parler==1.7',
    'django-permissions-widget==1.5.1',
    'django_polymorphic==1.2',
    'django-rest-polymorphic==0.1.8',
    'django-rest-swagger==2.1.2',
    'django-select-multiple-field==0.5.0a-draft',
    'django-singleton-admin==0.0.4',
    'django-subquery==1.0.4',
    'django-summernote==0.8.7.3',
    'django-taggit==0.22.1',
    'django-tenant-schemas==1.6.8',
    'django-tinymce==2.7.0',
    'django-tools==0.32.13',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.8.0',
    'djangorestframework-jwt==1.11.0',
    'djangorestframework==3.8.2',
    'dkimpy==0.6.1',
    'geocoder==1.37.0',
    'gunicorn==19.7.1',
    'html5lib==1.0b10',
    'influxdb==4.1.1',
    'lipisha==0.2.4',
    'lxml==3.7.3',
    'micawber==0.3.4',
    'mixpanel==4.3.2',
    'ndg-httpsclient==0.4.3',
    'openpyxl==2.4.8',
    'pendulum==1.2.4',
    'psycopg2==2.7.1',
    'pyasn1==0.4.2',
    'pygeoip==0.3.2',
    'pyjwt==1.5.3',
    'pyOpenSSL==17.5.0',
    'python-dateutil==2.6.1',
    'python-memcached==1.58',
    'python-social-auth==0.2.21',
    'surlex==0.2.0',
    'raven==6.1.0',
    'regex==2017.05.26',
    'requests==2.17.3',
    'schwifty==2.1.0',
    'sorl-thumbnail==12.3-github',
    'sorl-watermark==1.0.0',
    'South==1.0.2',
    'Sphinx==1.6.3',
    'stripe==2.11.0',
    'suds-jurko==0.6',
    'SurveyGizmo==1.2.2',
    'transifex-client==0.12.4',
    'unicodecsv==0.14.1',
    'wheel==0.29.0',
    'xlsxwriter==0.9.8',

    # Github requirements
    'django-tenant-extras==2.0.14',
    'django-fluent-contents==1.2.1-741ffae6',
    'django-bb-salesforce==1.2.2',
    'django-taggit-autocomplete-modified==0.1.1b1',
    'django-token-auth==0.3.10',
    'django-money-rates==0.3.1-github',
    'Flutterwave==1.1.0'
]

tests_requires = [
    'coverage==4.4.1',
    'coveralls==1.1',
    'pyyaml==3.12',
    'django-nose==1.4.4',
    'django-setuptest==0.2.1',
    'django-slowtests==0.5.1',
    'django-webtest==1.9.2',
    'factory-boy==2.8.1',
    'httmock==1.2.6',
    'mock==2.0.0',
    'nose==1.3.7',
    'pylint==1.7.2',
    'pyquery==1.2.17',
    'pylint-django==0.7.2',
    'tblib==1.3.2',
    'tdaemon==0.1.1',
    'WebTest==2.0.27'
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
    dependency_links=dependency_links,

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
