from django.test import SimpleTestCase

from bluebottle.utils.monkey_patch_tenant_migrations import (
    format_tenant_migration_progress,
)


class TenantMigrationProgressTests(SimpleTestCase):
    def test_format_progress(self):
        self.assertEqual(
            format_tenant_migration_progress(12, 43),
            'Tenant migrations: 12/43 - 27%',
        )

    def test_format_progress_complete(self):
        self.assertEqual(
            format_tenant_migration_progress(43, 43),
            'Tenant migrations: 43/43 - 100%',
        )

    def test_format_progress_empty(self):
        self.assertEqual(
            format_tenant_migration_progress(0, 0),
            'Tenant migrations: 0/0 - 100%',
        )
