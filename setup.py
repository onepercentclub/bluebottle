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
    'git+https://github.com/onepercentclub/django-token-auth.git@0.3.5#egg=django-token-auth-0.3.5',
    'git+https://github.com/st4lk/django-select-multiple-field.git@1dc7733008150a111cd141ff7c3f42bf4953dc7d#egg=django-select-multiple-field-0.5.0a-draft',
    'hg+https://bitbucket.org/jdiascarvalho/django-filetransfers@89c8381764da217d72f1fa396ce3929f0762b8f9#egg=django-filetransfers-0.1.1',
    'git+https://github.com/skada/django-money-rates@aeb2edf240471fac64f9cdf71e34f91d632f1b86#egg=django-money-rates-0.3.1-github'
]

install_requires = [
    'Babel==2.5.3',
    'Django==2.0.3',
    'Flutterwave==1.0.7',
    'Pillow==5.0.0',
    'South==1.0.2',
    'beautifulsoup4==4.6.0',
    'bleach==2.1.3',
    'bunch==1.0.1',
    'celery==4.1.0',
    'django-admin-sortable==2.1.3',
    'django-admin-tools==0.8.1',
    'django-celery==3.2.2',
    'django-choices==1.6.0',
    'django-cors-headers==2.2.0',
    'django-daterange-filter==1.3.0',
    'django-dynamic-fixture==2.0.0',
    'django-extensions==2.0.2',
    'django-exportdb==0.4.7',
    'django-filetransfers==0.1.0',
    'django-filter==1.1.0',
    'django-geoposition==0.3.0',
    'django-fluent-dashboard==1.0',
    'django-fsm==2.6.0',
    'django-hashers-passlib==0.4',
    'django-ipware==2.0.1',
    'django-localflavor==2.0',
    'django-lockdown==1.5.0',
    'django-loginas==0.3.3',
    'django-memoize==2.1.0',
    'django-modeltranslation==0.12.2',
    'django-parler==1.9.2',
    'django-polymorphic==2.0.2',
    'django-money==0.12.3',
    'django-rest-swagger==2.1.2',
    'django-select-multiple-field==0.4.2',
    'django-singleton-admin==0.0.4',
    'django-summernote==0.8.8.6',
    'django-taggit==0.22.2',
    'django-tenant-schemas==1.9.0',
    'django-tinymce==2.7.0',
    'django-tools==0.39.0',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.8.0',
    'djangorestframework-jwt==1.11.0',
    'djangorestframework==3.7.7',
    'dkimpy==0.7.1',
    'gunicorn==19.7.1',
    'html5lib==1.0.1',
    'influxdb==5.0.0',
    'lipisha==0.2.4',
    'lxml==4.1.1',
    'micawber==0.3.5',
    'mixpanel==4.3.2',
    'openpyxl==2.5.0',
    'pendulum==1.4.2',
    'psycopg2==2.7.4',
    'pygeoip==0.3.2',
    'pyjwt==1.6.0',
    'python-dateutil==2.6.1',
    'python-memcached==1.59',
    'python-social-auth==0.3.6',
    'surlex==0.2.0',
    'raven==6.6.0',
    'regex==2018.02.21',
    'requests==2.18.4',
    'schwifty==2.1.0',
    'sorl-thumbnail==12.4.1',
    'sorl-watermark==1.0.0',
    'South==1.0.2',
    'Sphinx==1.7.1',
    'suds-jurko==0.6',
    'SurveyGizmo==1.2.3',
    'transifex-client==0.13.1',
    'unicodecsv==0.14.1',
    'wheel==0.30.0',
    'xlsxwriter==1.0.2',

    # Github requirements
    'django-tenant-extras==2.0.14',
    'django-fluent-contents==2.0.2',
    'django-bb-salesforce==1.2.2',
    'django-taggit-autocomplete-modified==0.1.0',
    'django-token-auth==1.3.2b4',
    'django-money-rates==0.3.1'
]

tests_requires = [
    'coverage==4.5.1',
    'coveralls==1.3.0',
    'pyyaml==3.12',
    'django-nose==1.4.5',
    'django-setuptest==0.2.1',
    'django-webtest==1.9.2',
    'factory-boy==2.10.0',
    'httmock==1.2.6',
    'mock==2.0.0',
    'nose==1.3.7',
    'pylint==1.8.2',
    'pyquery==1.4.0',
    'pylint-django==0.9.1',
    'tblib==1.3.2',
    'tdaemon==0.1.1',
    'WebTest==2.0.29'
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
