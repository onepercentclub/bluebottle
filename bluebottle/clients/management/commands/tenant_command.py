import argparse

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from tenant_schemas.management.commands import InteractiveTenantOption as BaseInteractiveTenantOption


class InteractiveTenantOption(BaseInteractiveTenantOption):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("command_args", nargs=argparse.REMAINDER)


class Command(InteractiveTenantOption, BaseCommand):
    help = "Wrapper around django commands for use with an individual tenant"

    def handle(self, command, command_args, schema_name, *args, **options):
        tenant = self.get_tenant_from_options_or_interactive(
            schema_name=schema_name, **options
        )
        connection.set_tenant(tenant)
        del options['skip_checks']
        call_command(command, *command_args, *args, **options)
