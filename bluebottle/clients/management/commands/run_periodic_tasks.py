from django.core.management.base import BaseCommand
from django.db import connection
from tenant_schemas.management.commands import InteractiveTenantOption

from bluebottle.collect.models import CollectActivity
from bluebottle.deeds.models import Deed
from bluebottle.funding.models import Funding, Donor
from bluebottle.time_based.models import DateActivity, DateActivitySlot, PeriodActivity, TeamSlot, DateParticipant, \
    PeriodParticipant, TimeContribution


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
        models = [
            DateActivity, DateActivitySlot, DateParticipant,
            PeriodActivity, TeamSlot, PeriodParticipant,
            TimeContribution,
            Funding, Donor,
            Deed, CollectActivity
        ]

        for model in models:
            for task in model.get_periodic_tasks():
                task.execute()
