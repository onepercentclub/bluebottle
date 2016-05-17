#!/usr/bin/env python
import os
import sys

import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

readme = read_file('README.rst')
changes = ''

dependency_links = [
    'git+https://github.com/onepercentclub/django-taggit-autocomplete-modified.git@8e7fbc2deae2f1fbb31b574bc8819d9ae7c644d6#egg=django-taggit-autocomplete-modified-0.1.1b1',
    'git+https://github.com/onepercentclub/django-fluent-contents.git@8439c7ffc1ba8877247aa7d012928c9bb170dc79#egg=fluent_contents-1.0c3',
    'git+https://github.com/onepercentclub/django-bb-salesforce.git@1.1.18#egg=django-bb-salesforce-1.1.18',
    'git+https://github.com/onepercentclub/django-tenant-extras.git@2.0.0#egg=django-tenant-extras-2.0.0',
    'git+https://github.com/onepercentclub/django-token-auth.git@0.2.16#egg=django-token-auth-0.2.16'
]

install_requires = [
    'Babel==2.3.4',
    'BeautifulSoup==3.2.1',
    'Django==1.6.8',
    'Pillow==2.3.0',
    'South==1.0.2',
    'Sphinx==1.4.1',
    'bunch==1.0.1',
    'celery==3.1.23',
    'django-celery==3.1.17',
    'django-apptemplates==1.1.1',
    'django-choices==1.4.2',
    'django-compressor==1.3',
    'ember-compressor-compiler==0.3.1',
    'django-extensions==1.1.1',
    'django-exportdb==0.4.6',
    'django-filter==0.6',
    'django-geoposition==0.2.2',
    'django-localflavor==1.2',
    'django-modeltranslation==0.11',
    'django-social-auth==0.7.23',
    'django-taggit==0.12.1',
    'django-templatetag-handlebars==1.2.0',
    'django-tinymce==2.3.0',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.7.1',
    'django-dynamic-fixture==1.8.5',
    'django-fluent-dashboard==0.3.2',
    'djangorestframework==2.4.8',
    'dkimpy==0.5.4',
    'html5lib==0.9999999',
    'httmock==1.2.5',
    'micawber==0.3.3',
    'requests==2.5.1',
    'sorl-thumbnail==12.3',
    'transifex-client==0.11',
    'django-tools==0.25.0',
    'django-loginas==0.1.9',
    'pygraphviz==1.3.1',
    'beautifulsoup4==4.4.1',
    'psycopg2==2.6.1',
    'django-fsm==2.3.0',
    'suds-jurko==0.6',
    'django-ipware==1.1.5',
    'pygeoip==0.3.1',
    'python-social-auth==0.2.12',
    'python-memcached==1.57',
    'lxml==3.6.0',
    'unicodecsv==0.14.1',
    'python-dateutil==2.5.3',
    'gunicorn==19.2.1',
    'surlex==0.2.0',
    'django_polymorphic==0.6.1',
    'dnspython',
    'fabric',
    'django-tenant-schemas==1.5.8',
    'raven==5.16.0',
    'regex==2016.4.25',
    'djangorestframework-jwt==1.8.0',
    'django-filetransfers==0.1.0',
    'django-admin-tools==0.5.2',
    'django-rest-swagger==0.3.6',
    'django-lockdown==1.2',
    'mixpanel==4.3.0',
    'grequests==0.2.0',
    # Github requirements
    'django-taggit-autocomplete-modified==0.1.1b1',
    'django-fluent-contents==1.0c3',
    'django-bb-salesforce==1.1.18',
    'django-tenant-extras==2.0.0',
    'django-token-auth==0.2.16',
]

tests_requires = [
    'coverage==3.6',
    'django-nose==1.3',
    'django-setuptest==0.1.4',
    'factory-boy==2.3.1',
    'mock==1.0.1',
    'nose==1.3.4',
    'pylint==1.1.0',
    'tdaemon==0.1.1',
    'WebTest==2.0.18',
    'django-webtest==1.7.7',
    'pyquery==1.2.9'
]

dev_requires = [
    'ipdb'
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
