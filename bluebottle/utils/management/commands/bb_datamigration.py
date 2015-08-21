"""
Data migration creation command
"""

from __future__ import print_function

import sys
import os
import re
from optparse import make_option

try:
    set
except NameError:
    from sets import Set as set

from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import models
from django.conf import settings

from south.migration import Migrations
from south.exceptions import NoMigrations
from south.creator import freezer

from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--freeze', action='append', dest='freeze_list',
                    type='string',
                    help='Freeze the specified app(s). Provide an app name with each; use the option multiple times for multiple apps'),
        make_option('--stdout', action='store_true', dest='stdout',
                    default=False,
                    help='Print the migration to stdout instead of writing it to a file.'),
    )
    help = "Creates a new template data migration for the given app"
    usage_str = "Usage: ./manage.py datamigration appname migrationname [--stdout] [--freeze appname]"

    def handle(self, app=None, name="", freeze_list=None, stdout=False,
               verbosity=1, **options):

        # Any supposed lists that are None become empty lists
        freeze_list = freeze_list or []

        # --stdout means name = -
        if stdout:
            name = "-"

        # Only allow valid names
        if re.search('[^_\w]', name) and name != "-":
            self.error(
                "Migration names should contain only alphanumeric characters and underscores.")

        # if not name, there's an error
        if not name:
            self.error(
                "You must provide a name for this migration\n" + self.usage_str)

        if not app:
            self.error(
                "You must provide an app to create a migration for.\n" + self.usage_str)

        # Get the Migrations for this app (creating the migrations dir if needed)
        migrations = Migrations(app, force_creation=True,
                                verbose_creation=verbosity > 0)

        # See what filename is next in line. We assume they use numbers.
        new_filename = migrations.next_filename(name)

        # Work out which apps to freeze
        apps_to_freeze = self.calc_frozen_apps(migrations, freeze_list)

        # So, what's in this file, then?
        file_contents = MIGRATION_TEMPLATE % {
            "frozen_models": freezer.freeze_apps_to_string(apps_to_freeze),
            "complete_apps": apps_to_freeze and "complete_apps = [%s]" % (
            ", ".join(map(repr, apps_to_freeze))) or ""
        }

        # Custom Bluebottle
        # We find and replace the base apps with our mapped models
        for model in MODEL_MAP:
            model_map = MODEL_MAP[model]
            mapping = {
                'u"orm[\'{0}\']"'.format(model_map[
                                             'model']): '"orm[\'{0}\']".format(MODEL_MAP[\'{1}\'][\'model\'])'.format(
                    '{0}', model),
                'u\'{0}\''.format(
                    model_map['table']): 'MODEL_MAP[\'{0}\'][\'table\']'.format(
                    model),
                'u\'{0}\''.format(model_map[
                                      'model_lower']): 'MODEL_MAP[\'{0}\'][\'model_lower\']'.format(
                    model),
                'u\'{0}\''.format(
                    model_map['app']): 'MODEL_MAP[\'{0}\'][\'app\']'.format(
                    model),
                '[\'{0}\']'.format(
                    model_map['app']): '[MODEL_MAP[\'{0}\'][\'app\']]'.format(
                    model),
                'to=orm[\'{0}\']'.format(model_map[
                                             'model']): 'to=orm[MODEL_MAP[\'{0}\'][\'model\']]'.format(
                    model),
                '\'object_name\': \'{0}\''.format(model_map[
                                                      'class']): '\'object_name\': MODEL_MAP[\'{0}\'][\'class\']'.format(
                    model)
            }
            file_contents = reduce(lambda x, y: x.replace(y, mapping[y]),
                                   mapping, file_contents)

        # End Custom Bluebottle

        # - is a special name which means 'print to stdout'
        if name == "-":
            print(file_contents)
        # Write the migration file if the name isn't -
        else:
            fp = open(os.path.join(migrations.migrations_dir(), new_filename),
                      "w")
            fp.write(file_contents)
            fp.close()
            print("Created %s." % new_filename, file=sys.stderr)

    def calc_frozen_apps(self, migrations, freeze_list):
        """
        Works out, from the current app, settings, and the command line options,
        which apps should be frozen.
        """
        apps_to_freeze = []
        for to_freeze in freeze_list:
            if "." in to_freeze:
                self.error(
                    "You cannot freeze %r; you must provide an app label, like 'auth' or 'books'." % to_freeze)
            # Make sure it's a real app
            if not models.get_app(to_freeze):
                self.error(
                    "You cannot freeze %r; it's not an installed app." % to_freeze)
            # OK, it's fine
            apps_to_freeze.append(to_freeze)
        if getattr(settings, 'SOUTH_AUTO_FREEZE_APP', True):
            apps_to_freeze.append(migrations.app_label())
        return apps_to_freeze

    def error(self, message, code=1):
        """
        Prints the error, and exits with the given code.
        """
        print(message, file=sys.stderr)
        sys.exit(code)


MIGRATION_TEMPLATE = """# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from bluebottle.utils.model_dispatcher import get_model_mapping

MODEL_MAP = get_model_mapping()

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.

    def backwards(self, orm):
        "Write your backwards methods here."

    models = %(frozen_models)s

    %(complete_apps)s
    symmetrical = True
"""
