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
    'git+https://github.com/onepercentclub/django-tenant-extras.git@2.0.12#egg=django-tenant-extras-2.0.12',
    'git+https://github.com/mariocesar/sorl-thumbnail.git@v12.3#egg=sorl-thumbnail-12.3-github',
    'git+https://github.com/onepercentclub/django-token-auth.git@0.3.4#egg=django-token-auth-0.3.4',
    'git+https://github.com/st4lk/django-select-multiple-field.git@1dc7733008150a111cd141ff7c3f42bf4953dc7d#egg=django-select-multiple-field-0.5.0a-draft',
    'hg+https://bitbucket.org/jdiascarvalho/django-filetransfers@89c8381764da217d72f1fa396ce3929f0762b8f9#egg=django-filetransfers-0.1.1',
    'git+https://github.com/skada/django-money-rates@aeb2edf240471fac64f9cdf71e34f91d632f1b86#egg=django-money-rates-0.3.1-github'
]

install_requires = [
    'Babel==2.5.1',
    'Django==1.11.6',
    'Flutterwave==1.0.7',
    'Pillow==4.3.0',
    'South==1.0.2',
    'beautifulsoup4==4.6.0',
    'bleach==2.1.1',
    'bunch==1.0.1',
    'celery==4.1.0',
    'django-admin-sortable==2.1',
    'django-admin-tools==0.8.1',
    'django-celery==3.2.1',
    'django-choices==1.6.0',
    'django-cors-headers==2.1.0',
    'django-daterange-filter==1.3.0',
    'django-dynamic-fixture==1.9.5',
    'django-extensions==1.9.1',
    'django-exportdb==0.4.7',
    'django-filetransfers==0.1.0',
    'django-filter==1.0.4',
    'django-geoposition==0.3.0',
    'django-fluent-dashboard==1.0a1',
    'django-fsm==2.6.0',
    'django-hashers-passlib==0.3',
    'django-ipware==1.1.6',
    'django-localflavor==1.5.2',
    'django-lockdown==1.4.2',
    'django-loginas==0.3.3',
    'django-memoize==2.1.0',
    'django-modeltranslation==0.12.1',
    'django-parler==1.8',
    'django-polymorphic==1.3',
    'django-money==0.11.4',
    'django-rest-swagger==2.1.2',
    'django-select-multiple-field==0.4.2',
    'django-summernote==0.8.8.2',
    'django-taggit==0.22.1',
    'django-tenant-schemas==1.9.0',
    'django-tinymce==2.6.0',
    'django-tools==0.35.0',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.8.0',
    'djangorestframework-jwt==1.11.0',
    'djangorestframework==3.7.0',
    'dkimpy==0.6.2',
    'gunicorn==19.7.1',
    'html5lib==0.999999999',
    'influxdb==4.1.1',
    'lipisha==0.2.4',
    'lxml==4.0.0',
    'micawber==0.3.4',
    'mixpanel==4.3.2',
    'openpyxl==2.4.8',
    'pendulum==1.3.0',
    'psycopg2==2.7.3.1',
    'pygeoip==0.3.2',
    'pyjwt==1.5.3',
    'python-dateutil==2.6.1',
    'python-memcached==1.58',
    'python-social-auth==0.3.6',
    'surlex==0.2.0',
    'raven==6.2.1',
    'regex==2017.09.23',
    'requests==2.18.4',
    'sorl-thumbnail==12.3',
    'sorl-watermark==1.0.0',
    'South==1.0.2',
    'Sphinx==1.6.4',
    'suds-jurko==0.6',
    'SurveyGizmo==1.2.3',
    'transifex-client==0.12.4',
    'unicodecsv==0.14.1',
    'wheel==0.30.0',
    'xlsxwriter==1.0.0',

    # Github requirements
    'django-fluent-contents==1.2.1',
    'django-tenant-extras==2.0.12',
    'django-bb-salesforce==1.2.2',
    'django-taggit-autocomplete-modified==0.1.0',
    'django-token-auth==1.3.2b4',
    'django-money-rates==0.3.1'
]

tests_requires = [
    'coverage==4.4.1',
    'coveralls==1.2.0',
    'pyyaml==3.12',
    'django-nose==1.4.5',
    'django-setuptest==0.2.1',
    'django-webtest==1.9.2',
    'factory-boy==2.9.2',
    'httmock==1.2.6',
    'mock==2.0.0',
    'nose==1.3.7',
    'pylint==1.7.4',
    'pyquery==1.2.17',
    'pylint-django==0.7.2',
    'tblib==1.3.2',
    'tdaemon==0.1.1',
    'WebTest==2.0.28'
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
