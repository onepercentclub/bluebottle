Project Bluebottle
==================

.. image:: https://travis-ci.org/onepercentclub/bluebottle.png?branch=master
   :target: https://travis-ci.org/onepercentclub/bluebottle
.. image:: https://coveralls.io/repos/github/onepercentclub/bluebottle/badge.svg?branch=develop
   :target: https://coveralls.io/github/onepercentclub/bluebottle?branch=develop


The repository for Project Bluebottle, the crowdsourcing framework initiated
by the 1%Club.

Contributors
------------

For those who want to contribute to the BlueBottle project, it's easy to get
started:

#. Make sure you have a recent Python distro (2.7+ recommended).
#. Make sure (a recent) `virtualenv <http://pypi.python.org/pypi/virtualenv>`_ is installed.
#. Fork and/or clone the repository.
#. Navigate to your local repository directory.
#. Create a virtual environment within the repository directory, for example::

    $ virtualenv env
    $ source env/bin/activate

#. Create a secrets.py base on secrets.py.example

#. Install the project::

    $ pip install -e .[test] --process-dependency-links --trusted-host github.com
    $ python manage.py sync_schemas --shared --settings=bluebottle.settings.testing
    $ python manage.py migrate_schemas --shared --settings=bluebottle.settings.testing
    $ ... createtenant
    $ ...

#.  You're ready to roll now, baby!

Testing
-------

The BlueBottle test suite can be run completely using:

#. Get the latest Geodata

    $ curl https://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz | gunzip - > GeoIP.dat

#. Install the dependencies

    $ pip install -e .[test,dev]

#. Run the tests

    $ python manage.py test --settings=bluebottle.settings.testing

Website developers
------------------

For those who want to use BlueBottle as kickstart for their own website, it's
easy to add BlueBottle to your Django project.

#. Install the latest development version::

    $ pip install -e git://github.com/onepercentclub/bluebottle.git#egg=bluebottle
