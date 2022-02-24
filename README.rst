Project Bluebottle
==================

.. image:: https://travis-ci.org/onepercentclub/bluebottle.png?branch=master
   :target: https://travis-ci.org/onepercentclub/bluebottle
.. image:: https://coveralls.io/repos/github/onepercentclub/bluebottle/badge.svg?branch=master
   :target: https://coveralls.io/github/onepercentclub/bluebottle?branch=master
.. image:: https://requires.io/github/onepercentclub/bluebottle/requirements.svg?branch=master
   :target: https://requires.io/github/onepercentclub/bluebottle/requirements/?branch=master

The repository for Project Bluebottle, the crowdsourcing framework initiated
by GoodUp.

Contributors
------------

For those who want to try out to the BlueBottle project, here's to get
started:

#. Make sure you have a recent Python distro (3.7+ recommended).
#. Make sure (a recent) `virtualenv <http://pypi.python.org/pypi/virtualenv>`_ is installed.
#. Fork and/or clone the repository.
#. Navigate to your local repository directory.
#. Create a virtual environment within the repository directory, for example::

    $ virtualenv env
    $ source env/bin/activate

#. Create a `bluebottle/settings/local.py` base on `bluebottle/settings/secrets.py.example`

#. Install the project::

    $ pip install -e .[test]
    $ python manage.py migrate_schemas --shared --settings=bluebottle.settings.testing
    $ python manage.py  createtenant
    $ python manage.py runserver

#. You might still need to
    * Install libraries to get `pip install` working, like `libxmlsec1`, `postgresql`, `postgis`, `elasticsearch 6.x`.
    * Alter your hosts file (e.g. in `/etc/hosts` on Linux/OSX) to contain tenants you've created like::

        127.0.0.1 tenant35.localhost


Testing
-------

The BlueBottle test suite can be run completely using:

#. Install the dependencies

    $ pip install -e .[test,dev]

#. Create test db and restore testdata
    $ createdb test_reef
    $ psql test_reef < testdata.sql

#. Run the tests

    $ python manage.py test -k


Pull request - Testing, Reviewing and Merging Flow
------------
https://www.lucidchart.com/invitations/accept/89cab398-8c15-4701-8897-d2fef42c0aa7
