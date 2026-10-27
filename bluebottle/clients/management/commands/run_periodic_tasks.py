from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from tenant_schemas.management.commands import InteractiveTenantOption


class Command(InteractiveTenantOption, BaseCommand):
    help = "Run all periodic tasks for activities"

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--schema", dest="schema_name", help="specify tenant schema"
        )

    def handle(self, schema_name, *args, **options):
        tenant = self.get_tenant_from_options_or_interactive(
            schema_name=schema_name, **options
        )
        connection.set_tenant(tenant)

        # Find all models that have the get_periodic_tasks method and execute their tasks
        for model in apps.get_models():
            if hasattr(model, 'get_periodic_tasks') and callable(getattr(model, 'get_periodic_tasks', None)):
                try:
                    if model.get_periodic_tasks():
                        print(f"Running tasks for {model.__name__}")
                    for task in model.get_periodic_tasks():
                        print(f"- {task}")
                        task.execute()
                except Exception:
                    # Skip models that raise exceptions when calling get_periodic_tasks
                    continue
