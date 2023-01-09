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

#. (optional) If you want to use Docker for Postgres and Elasticsearch, run the steps below. Make sure to download Docker (e.g. `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_) first.
    * To start the containers::

        $ docker-compose -u -d

    * To import a database dump file (please note that the last two commands run without the `-t` flag)::

        $ docker exec -it -u postgres postgres dropdb reef
        $ docker exec -it -u postgres postgres createdb reef
        $ bzcat reef-prod-current.sql.bz2 | docker exec -i -u postgres postgres psql reef
        $ echo "UPDATE clients_client SET domain_url=CONCAT(client_name, '.localhost');" | docker exec -i -u postgres postgres psql reef

#. Migrate the database schemas::

    $ python manage.py migrate_schemas --shared --settings=bluebottle.settings.testing

#. (optional) Create a new tenant (if you haven't imported a database dump)::

    $ python manage.py create_tenant

#. (optional) Re-index any imported data using Elasticsearch
    * For all tenants::
    
        $ python manage.py tenant_command search_index --rebuild -f

    * If for whatever reason this doesn't work, try running the migration step for a single tenant only, and indexing that tenant's data. E.g.::

        $ python manage.py migrate_schemas -s onepercent --settings=bluebottle.settings.testing
        $ python manage.py tenant_command --schema onepercent search_index --rebuild -f

#. Start the server::

    $ python manage.py runserver

#. You might still need to
    * Install libraries to get `pip install` working, like `libxmlsec1`, `postgresql`, `postgis`, `elasticsearch 6.x`
        * Installing Elasticsearch is not necessary when using Docker

    * Alter your hosts file (e.g. in `/etc/hosts` on Linux/OSX) to contain tenants you've created like::

        127.0.0.1 tenant35.localhost

Docker
------

It is possible to run PostgreSQL and Elasticsearch in a Docker environment using `docker-compose`. To get started, make sure to download a Docker client, like `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_.

In your `local.py` file, set the `DATABASES` variable to the following::

    DATABASES = {
        'default': {
            'ENGINE': 'bluebottle.clients.postgresql_backend',
            'HOST': 'localhost',
            'PORT': '5432',
            'NAME': 'reef',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'DISABLE_SERVER_SIDE_CURSORS': True # this prevents issues with connection pooling
        },
    }

To run the containers::

    $ docker-compose -u -d

To shut them down::

    $ docker-compose down

The environment also comes with pgAdmin included so you can inspect the local database. Navigate to `http://localhost:5050` and login with these credentials:

    * Email: `admin@admin.com`
    * Password: `admin`

After that, you can add a new server using the details below to inspect the PostgreSQL database:

    * Host: `host.docker.internal`
    * Username: `postgres`
    * Password: `postgres`


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
