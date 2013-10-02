#!/usr/bin/env python
import os
import sys

import bluebottle
from setuptools import setup, find_packages


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

   
readme = read_file('README.md')
changes = ''
#changes = read_file('CHANGES.rst')


install_requires = [
#    'Babel==1.3',
#    'BeautifulSoup==3.2.1',
    'Django==1.5.4',
#    'Jinja2==2.7',
    'Pillow==2.1.0',
    'South==0.8.1',
    'Sphinx==1.2b1',
#    'cssmin==0.1.4',
#    'django-admin-tools==0.5.1',
#    'django-celery==3.0.17',
    'django-choices==1.1.11',
#    'django-compressor==1.2',
#    'django-countries==1.5',
#    'django-debug-toolbar==0.9.4',
#    'django-docdata==0.1',
    'django-extensions==1.1.1',
#    'django-filetransfers==0.0.0',
#    'django-filter==0.6',
#    'django-fluent-contents==0.9a1',
#    'django-fluent-dashboard==0.3.2',
#    'django-iban==0.2.1',
#    'django-jenkins==0.14.0',
#    'django-localflavor==1.0',
#    'django-polymorphic==0.5',
    'django-registration==0.8',
#    'django-salesforce==0.1.6.3',
#    'django-social-auth==0.7.23',
#    'django-statici18n==0.4.5',
    'django-taggit==0.10a1',
    'django-taggit-autocomplete-modified==0.1.0b4',
#    'django-templatetag-handlebars==1.2.0',
#    'django-tinymce==1.5.1b2',
#    'django-wysiwyg==0.5.1',
    'djangorestframework==2.3.6',
#    'dkimpy==0.5.4',
#    'dnspython==1.11.0',
#    'html5lib==0.95',
#    'jsmin==2.0.2',
#    'micawber==0.2.6',
#    'pycurl==7.19.0',
#    'pytz==2013b',
#    'raven==3.3.12',
#    'requests==1.2.3',
#    'selenium==2.33.0',
    'sorl-thumbnail==11.12',
#    'splinter==0.5.3',
#    'suds-jurko==0.4.1.jurko.5.-development-',
    'surlex==0.1.2',
    'transifex-client==0.9',
]


dependency_links = [
    'https://bitbucket.org/onepercentclub/suds/get/afe727f50704.zip#egg=suds-jurko-0.4.1.jurko.5.-development-',

    'https://github.com/onepercentclub/django-salesforce/archive/1e54beb7bcc15a893e9590fb27cbf08853da5599.zip#egg=django-salesforce-0.1.6.3',
    
    # There hasn't been a release of django-registration is a while and we need the 1.5 custom user support.
    # Official: https://bitbucket.org/ubernostrum/django-registration/
    # Fork with 1.5 Custom User support: https://bitbucket.org/eire1130/django-registration
    # Our fork of the fork with HTML_ACTIVATION_EMAIL option:
    # TODO Try to unwind this mess and contribute some stuff upstream.
    'https://bitbucket.org/onepercentclub/django-registration/get/ae9e9ed265ed.zip#egg=django-registration-0.8',

    'https://bitbucket.org/wkornewald/django-filetransfers/get/32ddeac.zip#egg=django-filetransfers-0.0.0',

    'https://github.com/onepercentclub/django-docdata/archive/120ae5b8a1da6152d43d4601edc8832268e05515.zip#egg=django-docdata-0.1',
]


tests_require = [
    'coverage==3.6',
    'django-nose==1.1',
    'mock==1.0.1',
    'nose==1.3.0',
    'pylint==0.28.0',
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
    description='Bluebottle, the crowdsourcing framework initiated by the 1%CLUB.',
    long_description='\n\n'.join([readme, changes]),
    author='1%CLUB',
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
