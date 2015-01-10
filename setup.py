#!/usr/bin/env python
import os
import sys

import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

readme = read_file('README.rst')
changes = ''

install_requires = [
    'Babel==1.3',
    'bunch==1.0.1',
    'Django==1.6.8',
    'Pillow==2.3.0',
    'South==1.0',
    'Sphinx==1.2b1',
    'django-celery==3.0.17',
    'django-apptemplates==0.0.1',
    'django-choices==1.1.11',
    'django-compressor==1.3',
    'ember-compressor-compiler==0.3.1',
    'django-extensions==1.1.1',
    'django-filter==0.6',
    'django-fluent-contents==1.0c3',
    'django-iban==0.2.1',
    'django-localflavor==1.0',
    'django-social-auth==0.7.23',
    'django-statici18n==0.4.5',
    'django-taggit==0.12.1',
    'django-templatetag-handlebars==1.2.0',
    'django-tinymce==1.5.2',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.5.1',
    'django-dynamic-fixture==1.8.0',
    'django-fluent-dashboard==0.3.2',
    'djangorestframework==2.3.12',
    'dkimpy==0.5.4',
    'html5lib==0.95',
    'micawber==0.2.6',
    'requests==2.3.0',
    'sorl-thumbnail==11.12',
    'transifex-client==0.9.1',
    'django-tools==0.25.0',
    'django-loginas==0.1.3',
    'pygraphviz==1.2',
    'beautifulsoup4==4.3.2',
    'psycopg2==2.2.1',
    'django-fsm==1.6.0',
    'suds-jurko==0.6',
    'django-ipware==0.0.8',
    'pygeoip==0.3.1',
    'python-social-auth==0.1.26',
    'python-memcached==1.53',
    'lxml==3.1.2',
    'unicodecsv==0.9.4',
    'python-dateutil==1.5',
    'gunicorn==0.14.6',
    'surlex==0.2.0',
    'django_polymorphic==0.5.6',
    'dnspython',
    'fabric',

    # Github requirements
    'djangorestframework-jwt',
    'django-salesforce',
    'django-taggit-autocomplete-modified==0.1.0b4',
    'django-tenant-schemas',

    # Bitbucket requirements
    'django-filetransfers',
    'django-admin-tools',
    'django-registration'

]


dependency_links = [

    'https://github.com/GetBlimp/django-rest-framework-jwt/archive/b6b42b967c3584b426446df1f72149b7a07fd520.zip#egg=djangorestframework-jwt',
    'https://github.com/onepercentclub/django-salesforce/archive/1e54beb7bcc15a893e9590fb27cbf08853da5599.zip#egg=django-salesforce',
    'https://github.com/onepercentclub/legacyauth/archive/3f2406c50dead25a748fb2433de55b73a9162f18.zip#egg=legacyauth',
    'https://github.com/mrmachine/django-taggit-autocomplete-modified/archive/8e41e333ce1f0690e1041515b1f2cbf12e0452ce.zip#egg=django-taggit-autocomplete-modified-0.1.0b4',
    'https://github.com/bernardopires/django-tenant-schemas/archive/v1.5.1.zip#egg=django-tenant-schemas',

    'https://bitbucket.org/wkornewald/django-filetransfers/get/32ddeac.zip#egg=django-filetransfers',
    'https://bitbucket.org/sergei_maertens/django-admin-tools/get/c989fd1.zip#egg=django-admin-tools',
    'https://bitbucket.org/onepercentclub/django-registration/get/ae9e9ed265ed.zip#egg=django-registration',
]

tests_require = install_requires + [
    'coverage==3.6',
    'django-nose==1.3',
    'django-setuptest==0.1.4',
    'factory-boy==2.3.1',
    'mock==1.0.1',
    'nose==1.3.4',
    'pylint==1.1.0',
    'sauceclient==0.1.0',
    'selenium==2.44.0',
    'splinter==0.6.0',
    'tdaemon==0.1.1'
]

setup(
    name='bluebottle',
    version='.'.join(map(str, bluebottle.__version__)),
    license='BSD',

    # Packaging.
    packages=find_packages(exclude=('tests', 'tests.*')),
    install_requires=install_requires,
    dependency_links=dependency_links,
    tests_require=tests_require,
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
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
    ],
)
