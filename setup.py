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
    'git+https://github.com/onepercentclub/django-tenant-extras.git@1.9.3#egg=django-tenant-extras-1.9.3',
    'git+https://github.com/onepercentclub/django-token-auth.git@0.2.6#egg=django-token-auth-0.2.6'
]

install_requires = [
    'Babel==1.3',
    'BeautifulSoup==3.2.1',
    'Django==1.6.8',
    'Pillow==2.3.0',
    'South==1.0',
    'Sphinx==1.2b1',
    'bunch==1.0.1',
    'celery==3.1.17',
    'django-celery==3.0.17',
    'django-apptemplates==0.0.1',
    'django-choices==1.1.11',
    'django-compressor==1.3',
    'ember-compressor-compiler==0.3.1',
    'django-extensions==1.1.1',
    'django-exportdb==0.4.5',
    'django-filter==0.6',
    'django-geoposition==0.2.2',
    'django-iban==0.2.1',
    'django-localflavor==1.1',
    'django-social-auth==0.7.23',
    'django-taggit==0.12.1',
    'django-templatetag-handlebars==1.2.0',
    'django-tinymce==1.5.2',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.5.1',
    'django-dynamic-fixture==1.8.0',
    'django-fluent-dashboard==0.3.2',
    'djangorestframework==2.3.14',
    'dkimpy==0.5.4',
    'html5lib==0.95',
    'httmock==1.2.3',
    'micawber==0.2.6',
    'requests==2.3.0',
    'sorl-thumbnail==11.12',
    'transifex-client==0.11b3',
    'django-tools==0.25.0',
    'django-loginas==0.1.3',
    'pygraphviz==1.2',
    'beautifulsoup4==4.3.2',
    'psycopg2==2.5.5',
    'django-fsm==1.6.0',
    'suds-jurko==0.6',
    'django-ipware==0.0.8',
    'pygeoip==0.3.1',
    'python-social-auth==0.2.12',
    'python-memcached==1.53',
    'lxml==3.4.4',
    'unicodecsv==0.9.4',
    'python-dateutil==1.5',
    'gunicorn==19.2.1',
    'surlex==0.2.0',
    'django_polymorphic==0.6.1',
    'dnspython',
    'fabric',
    'django-tenant-schemas==1.5.2',
    'raven==5.1.1',
    'djangorestframework-jwt==1.1.1',
    'django-filetransfers==0.1.0',
    'django-admin-tools==0.5.2',
    'django-rest-swagger==0.3.4',

    # Github requirements
    'django-taggit-autocomplete-modified==0.1.1b1',
    'django-fluent-contents==1.0c3',
    'django-bb-salesforce==1.1.18',
    'django-token-auth==0.2.6',
    'django-tenant-extras==1.9.3'
]

tests_requires = [
    'coverage==3.6',
    'django-nose==1.3',
    'django-setuptest==0.1.4',
    'factory-boy==2.3.1',
    'mock==1.0.1',
    'nose==1.3.4',
    'pylint==1.1.0',
    'tdaemon==0.1.1'
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
