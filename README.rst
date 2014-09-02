Project Bluebottle
==================

.. image:: https://travis-ci.org/onepercentclub/bluebottle.png?branch=master
   :target: https://travis-ci.org/onepercentclub/bluebottle


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

#. Install the project::

    $ python setup.py develop

#.  You're ready to roll now, baby!

Testing
-------

The BlueBottle test suite can be run completely using:

    python setup.py test

***Watching with Guard***

The tests can be automatically run when changed using
guard. To install and run do:

    gem install bundler
    bundle
    bundle exec guard start

Guard will run the whole test suite when starting, 
run specific test files when they change, and run
an apps test suite when the apps code changes.

***Frontend Javascript***

From the root of the application (node/npm required):

    npm install
    grunt

This will install some npm & bower packages for dev & testing, 
and run the tests headless with PhantomJS using Karma. 
Karma is watching the test/ directory for changes.


Website developers
------------------

For those who want to use BlueBottle as kickstart for their own website, it's
easy to add BlueBottle to your Django project.

#. Install the latest development version::

    $ pip install -e git://github.com/onepercentclub/bluebottle.git#egg=bluebottle
