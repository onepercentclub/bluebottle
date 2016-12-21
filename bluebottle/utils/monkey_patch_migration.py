import importlib

from django.apps.registry import apps as global_apps
from django.db import migrations
from django.db.migrations.executor import MigrationExecutor

migration = importlib.import_module('fluent_contents.plugins.text.migrations.0002_textitem_text_final')

migration.Migration.initial = True


def detect_soft_applied(self, project_state, migration):
    """
    Tests whether a migration has been implicitly applied - that the
    tables or columns it would create exist. This is intended only for use
    on initial migrations (as it only looks for CreateModel and AddField).
    """
    if migration.initial is None:
        # Bail if the migration isn't the first one in its app
        if any(app == migration.app_label for app, name in migration.dependencies):
            return False, project_state
    elif migration.initial is False:
        # Bail if it's NOT an initial migration
        return False, project_state

    if project_state is None:
        after_state = self.loader.project_state((migration.app_label, migration.name), at_end=True)
    else:
        after_state = migration.mutate_state(project_state)
    apps = after_state.apps
    found_create_model_migration = False
    found_add_field_migration = False
    existing_table_names = self.connection.introspection.table_names(self.connection.cursor())
    # Make sure all create model and add field operations are done
    for operation in migration.operations:
        if isinstance(operation, migrations.CreateModel):
            model = apps.get_model(migration.app_label, operation.name)
            if model._meta.swapped:
                # We have to fetch the model to test with from the
                # main app cache, as it's not a direct dependency.
                model = global_apps.get_model(model._meta.swapped)
            if model._meta.proxy or not model._meta.managed:
                continue
            if model._meta.db_table not in existing_table_names:
                return False, project_state
            found_create_model_migration = True
        elif isinstance(operation, migrations.AddField):
            model = apps.get_model(migration.app_label, operation.model_name)
            if model._meta.swapped:
                # We have to fetch the model to test with from the
                # main app cache, as it's not a direct dependency.
                model = global_apps.get_model(model._meta.swapped)
            if model._meta.proxy or not model._meta.managed:
                continue

            table = model._meta.db_table
            field = model._meta.get_field(operation.name)

            if table not in existing_table_names:
                return False, project_state

            # Handle implicit many-to-many tables created by AddField.
            if field.many_to_many:
                if field.remote_field.through._meta.db_table not in existing_table_names:
                    return False, project_state
                else:
                    found_add_field_migration = True
                    continue

            column_names = [column.name for column in
                            self.connection.introspection.get_table_description(self.connection.cursor(), table)]
            if field.column not in column_names:
                return False, project_state
            found_add_field_migration = True
    # If we get this far and we found at least one CreateModel or AddField migration,
    # the migration is considered implicitly applied.
    return (found_create_model_migration or found_add_field_migration), after_state


MigrationExecutor.detect_soft_applied = detect_soft_applied
