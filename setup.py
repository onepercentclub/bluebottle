#!/usr/bin/env python
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
    'git+https://github.com/onepercentclub/django-tenant-extras.git@2.0.8#egg=django-tenant-extras-2.0.8',
    'git+https://github.com/onepercentclub/django-token-auth.git@0.3.0#egg=django-token-auth-0.3.0',
    'git+https://github.com/mariocesar/sorl-thumbnail.git@v12.3#egg=sorl-thumbnail-12.3-github',
    'hg+https://bitbucket.org/jdiascarvalho/django-filetransfers@89c8381764da217d72f1fa396ce3929f0762b8f9#egg=django-filetransfers-0.1.1'
]

install_requires = [
    'Babel==2.3.4',
    'beautifulsoup4==4.4.1',
    'BeautifulSoup==3.2.1',
    'bunch==1.0.1',
    'celery==3.1.23',
    'django-admin-tools==0.7.2',
    'django-celery==3.1.17',
    'django-choices==1.4.2',
    'django-dynamic-fixture==1.8.5',
    'django-exportdb==0.4.6',
    'django-extensions==1.6.7',
    'django-filetransfers==0.1.1',
    'django-filter==0.13.0',
    'django-fluent-dashboard==0.6.1',
    'django-fsm==2.4.0',
    'django-geoposition==0.2.2',
    'django-ipware==1.1.5',
    'django-localflavor==1.2',
    'django-lockdown==1.2',
    'django-loginas==0.1.9',
    'django-modeltranslation==0.11',
    'django-money==0.8',
    'django-rest-swagger==0.3.6',
    'django-taggit==0.18.3',
    'django-tenant-schemas==1.6.2',
    'django-tinymce==2.3.0',
    'django-tools==0.30.0',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.7.1',
    'Django==1.9.6',
    'django_polymorphic==0.9.2',
    'djangorestframework-jwt==1.8.0',
    'djangorestframework==3.3.3',
    'dkimpy==0.5.6',
    'fabric',
    'gunicorn==19.5.0',
    'lxml==3.6.0',
    'micawber==0.3.3',
    'mixpanel==4.3.0',
    'Pillow==3.2.0',
    'psycopg2==2.6.1',
    'pygeoip==0.3.2',
    'python-dateutil==2.5.3',
    'python-memcached==1.57',
    'python-social-auth==0.2.19',
    'raven==5.16.0',
    'regex==2016.4.25',
    'requests==2.5.1',
    'sorl-thumbnail==12.3-github',
    'South==1.0.2',
    'Sphinx==1.4.1',
    'suds-jurko==0.6',
    'surlex==0.2.0',
    'transifex-client==0.11',
    'unicodecsv==0.14.1',
    'wheel==0.29.0',

    # Github requirements
    'django-bb-salesforce==1.2.2',
    'django-cors-headers==1.1.0',
    'django-fluent-contents==1.1.4',
    'django-taggit-autocomplete-modified==0.1.1b1',
    'django-tenant-extras==2.0.8',
    'django-token-auth==0.3.0'
]

tests_requires = [
    'coverage==4.0.3',
    'django-nose==1.4.3',
    'django-setuptest==0.2.1',
    'django-webtest==1.7.9',
    'factory-boy==2.7.0',
    'httmock==1.2.5',
    'mock==2.0.0',
    'nose==1.3.7',
    'pylint==1.5.5',
    'pyquery==1.2.13',
    'tdaemon==0.1.1',
    'WebTest==2.0.21'
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
