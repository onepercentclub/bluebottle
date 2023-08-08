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

#. Fork and/or clone the repository.
#. Navigate to your local repository directory.
#. Create a `bluebottle/settings/local.py` base on `bluebottle/settings/secrets.py.example`

Now you have the option to install the application with, or without Docker. If you wish to not use Docker, continue below. Otherwise, see :ref:`docker`.

#. Create a virtual environment within the repository directory, for example::

    $ virtualenv env
    $ source env/bin/activate

#. Make sure you have a recent Python distro (3.7+ recommended).
#. Make sure (a recent) `virtualenv <http://pypi.python.org/pypi/virtualenv>`_ is installed.
#. Install the project::

    $ pip install -e .[test]

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
        * Installing these is not necessary when using Docker

    * Alter your hosts file (e.g. in `/etc/hosts` on Linux/OSX) to contain tenants you've created like::

        127.0.0.1 tenant35.localhost

.. _docker:

Docker
------

It is possible to run thy Python server, PostgreSQL and Elasticsearch in a Docker environment using `docker-compose`. To get started, make sure to download a Docker client, like `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_.

Installation:
~~~~~~~~~~~~~

Make sure to download Docker (e.g. `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_) first.

In your `local.py` file, set the `DATABASES` variable to the following::

    DATABASES = {
        'default': {
            'ENGINE': 'bluebottle.clients.postgresql_backend',
            'HOST': 'postgres',
            'PORT': '5432',
            'NAME': 'reef',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'DISABLE_SERVER_SIDE_CURSORS': True # this prevents issues with connection pooling
        },
    }

    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': 'elasticsearch:9200'
        },
    }

* To start the containers (if this is your first time, all dependencies will be installed automatically)::

    $ docker-compose -u -d

* To import a database dump file (please note that the last two commands run without the `-t` flag)::

    $ docker exec -it -u postgres postgres dropdb reef
    $ docker exec -it -u postgres postgres createdb reef
    $ bzcat reef-prod-current.sql.bz2 | docker exec -i -u postgres postgres psql reef
    $ echo "UPDATE clients_client SET domain_url=CONCAT(client_name, '.localhost');" | docker exec -i -u postgres postgres psql reef

* If you are running into errors related to max_map_count, then run the following command in your terminal: `sysctl -w vm.max_map_count=262144`

Running the containers:
~~~~~~~~~~~~~~~~~~~~~~~

To run the containers::

    $ docker-compose -u -d


To run one specific container::

    $ docker-compose -u -d [CONTAINER_NAME]

Or on other systems (some OSX)::

    $ docker compose up -d elasticsearch


To shut them down::

    $ docker-compose down

The environment also comes with pgAdmin included so you can inspect the local database. Navigate to `http://localhost:5050` and login with these credentials:

    * Email: `admin@admin.com`
    * Password: `admin`

After that, you can add a new server using the details below to inspect the PostgreSQL database:

    * Host: `host.docker.internal`
    * Username: `postgres`
    * Password: `postgres`

To run commands in the Python container::

    $ docker exec -it bluebottle python manage.py [YOUR_COMMAND]

    - For example::
  
        $ docker exec -it bluebottle python manage.py migrate_schemas -s onepercent --settings=bluebottle.settings.local

If you need to rebuild the container, for example when you want to apply changes after pulling the latest version of a branch, run::

    $ docker compose up --build

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
