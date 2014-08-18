#!/usr/bin/env python
import os
import sys

import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


readme = read_file('README.rst')
changes = ''
#changes = read_file('CHANGES.rst')


install_requires = [
    'Babel==1.3',
    'Django==1.5.5',
    'Pillow==2.3.0',
    'South==0.8.1',
    'Sphinx==1.2b1',
    'django-admin-tools==0.5.1', # for now replaced by fork
    'django-apptemplates==0.0.1',
    'django-choices==1.1.11',
    'django-compressor==1.2',
    'django-extensions==1.1.1',
    'django-filetransfers==0.0.0',
    'django-filter==0.6',
    'django-fluent-contents==0.9a1', # Version 1.0b1 and up breaks our code
    'django-iban==0.2.1',
    'django-localflavor==1.0',
    'django-registration==1.0',
    'django-social-auth==0.7.23',
    'django-statici18n==0.4.5',
    'django-taggit==0.10a1',
    'django-taggit-autocomplete-modified==0.1.0b4',
    'django-templatetag-handlebars==1.2.0',
    'django-tinymce==1.5.1b2',
    'django-uuidfield==0.5.0',
    'django-wysiwyg==0.5.1',
    'djangorestframework==2.3.12',
    'dkimpy==0.5.4',
    'html5lib==0.95',
    'micawber==0.2.6',
    'mock==1.0.1',
    'requests==2.3.0',
    'sorl-thumbnail==11.12',
    'splinter==0.6.0',
    'transifex-client==0.9',
    'django-tools==0.25.0',
    'django-loginas==0.1.3',
    'pygraphviz==1.2',
    'beautifulsoup4==4.3.2',
    # JSON Web Token based authentication for Django REST framework
    'djangorestframework-jwt==0.1.5',
    'psycopg2==2.2.1'
]


dependency_links = [
    'https://github.com/onepercentclub/django-rest-framework-jwt/archive/master.zip#egg=djangorestframework-jwt-0.1.5',

    'https://bitbucket.org/onepercentclub/suds/get/afe727f50704.zip#egg=suds-jurko-0.4.1.jurko.5.-development-',

    'https://github.com/onepercentclub/django-salesforce/archive/1e54beb7bcc15a893e9590fb27cbf08853da5599.zip#egg=django-salesforce-0.1.6.3',

    'https://bitbucket.org/wkornewald/django-filetransfers/get/32ddeac.zip#egg=django-filetransfers-0.0.0',

    'https://bitbucket.org/sergei_maertens/django-admin-tools/get/c989fd1.zip#egg=django-admin-tools-0.5.1',
]

# TODO: update
tests_require = [
    'coverage==3.6',
    'django-nose',
    'django-admin-tools==0.5.1',
    'django-apptemplates==0.0.1',
    'django_compressor==1.2',
    'django-fluent-contents==0.9a1', # Version 1.0b1 and up breaks our code
    'django-filetransfers==0.0.0',
    'django-localflavor==1.0',
    'django-registration==1.0',
    'django-setuptest==0.1.4',
    'django-social-auth==0.7.23',
    'django-taggit==0.10a1',
    'django-templatetag-handlebars==1.2.0',
    'django-tinymce==1.5.1b2',
    'django-wysiwyg==0.5.1',
    'djangorestframework==2.3.12',
    'factory-boy==2.3.1',
    'micawber==0.2.6',
    'mock==1.0.1',
    'mollie-api-python==1.0.0',
    'nose==1.3.3',
    'pylint==1.1.0',
    'requests==2.3.0',
    'sauceclient==0.1.0',
    'selenium==2.42.1',
    'South==0.8.1', # Functional testing libraries
    'sorl-thumbnail==11.12',
    'splinter==0.6.0', # Functional testing libraries
    'django-tools==0.25.0',
    'django-loginas==0.1.3',
    'tdaemon==0.1.1',
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

    # tests
    test_suite='bluebottle.test.suite.BlueBottleTestSuite',
)
