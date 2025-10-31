Email Message Preview System
============================

The Bluebottle project includes a comprehensive email preview system for all TransitionMessage classes across the codebase.

Location
--------

All preview-related files are in: ``bluebottle/notifications/``

Quick Start
-----------

Generate all email previews with English and Dutch translations::

    $ python manage.py preview_all_messages --all --all-languages

View the interactive gallery::

    # Via Django server (recommended for multi-tenant)
    $ python manage.py runserver --settings=bluebottle.settings.local
    # Visit: http://[tenant].localhost:8000/static/assets/email_previews/index_all.html
    # Example: http://onepercent.localhost:8000/static/assets/email_previews/index_all.html

    # Or open directly
    $ xdg-open bluebottle/notifications/static/email_previews/index_all.html

Features
--------

* **167 Messages Discovered** - Automatically finds all TransitionMessage classes
* **146 Previews Generated** - HTML previews in both English and Dutch
* **Interactive Gallery** - Modal previews with language switching
* **16 Modules Organized** - Groups by source module (activities, funding, etc.)
* **Smart Mocking** - Automatic mock objects for different message types
* **No Database Required** - Pure mock-based rendering

Command Options
---------------

List all available modules::

    $ python manage.py preview_all_messages --list-modules

Generate specific module::

    $ python manage.py preview_all_messages --module activities
    $ python manage.py preview_all_messages --module funding

English only (faster)::

    $ python manage.py preview_all_messages --all

Custom output directory::

    $ python manage.py preview_all_messages --all --output-dir /tmp/previews

Gallery Features
----------------

* **Modal Previews**: Click any email to open it in a full-screen modal
* **Language Switcher**: Toggle between English (EN) and Dutch (NL)
* **Module Organization**: Messages grouped by their source module
* **Statistics Dashboard**: See message counts by category
* **Keyboard Navigation**: Press ESC to close modals
* **Responsive Design**: Works on desktop and mobile

Documentation
-------------

* **User Guide**: ``bluebottle/notifications/README_EMAIL_PREVIEWS.md``
* **Technical Overview**: ``bluebottle/notifications/PREVIEW_SYSTEM.md``
* **Migration Summary**: ``MIGRATION_COMPLETE.md`` (project root)

Adding New Messages
-------------------

When you create a new TransitionMessage subclass:

1. No configuration needed - autodiscovery will find it
2. Regenerate previews::

    $ python manage.py preview_all_messages --all --all-languages

3. Refresh the gallery in your browser

File Structure
--------------

::

    bluebottle/notifications/
    ├── management/commands/
    │   └── preview_all_messages.py    # Main command
    ├── static/email_previews/          # Generated previews (gitignored)
    │   ├── index_all.html              # Interactive gallery
    │   ├── metadata_all.json           # Message metadata
    │   └── [module_folders]/           # Organized by module
    ├── README_EMAIL_PREVIEWS.md        # User guide
    └── PREVIEW_SYSTEM.md               # Technical overview

Troubleshooting
---------------

**Command not found**

Make sure you're using the correct Python environment::

    $ ~/.virtualenvs/bluebottle/bin/python manage.py preview_all_messages --all

**Import errors**

Ensure Django is properly configured::

    $ export DJANGO_SETTINGS_MODULE=bluebottle.settings.local
    $ python manage.py preview_all_messages --all

**Preview not updating**

Delete the output directory and regenerate::

    $ rm -rf bluebottle/notifications/static/email_previews
    $ python manage.py preview_all_messages --all --all-languages

For More Information
--------------------

See the detailed documentation in ``bluebottle/notifications/README_EMAIL_PREVIEWS.md``

