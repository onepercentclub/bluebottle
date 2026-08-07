import functools
import multiprocessing
import sys

from django.conf import settings

from tenant_schemas.migration_executors import parallel as parallel_module
from tenant_schemas.migration_executors import standard as standard_module
from tenant_schemas.migration_executors.base import run_migrations


def format_tenant_migration_progress(completed, total):
    if total <= 0:
        percent = 100
    else:
        percent = int(100 * completed / total)
    return 'Tenant migrations: {}/{} - {}%'.format(completed, total, percent)


def write_tenant_migration_progress(completed, total):
    sys.stdout.write(format_tenant_migration_progress(completed, total) + '\n')
    sys.stdout.flush()


def _should_show_progress(options):
    return int(options.get('verbosity', 1)) >= 1


def run_tenant_migrations_with_progress_standard(self, tenants):
    tenants = list(tenants)
    total = len(tenants)
    show_progress = _should_show_progress(self.options)

    for index, schema_name in enumerate(tenants, start=1):
        run_migrations(self.args, self.options, self.codename, schema_name)
        if show_progress:
            write_tenant_migration_progress(index, total)


def run_tenant_migrations_with_progress_parallel(self, tenants):
    tenants = list(tenants)
    total = len(tenants)
    if not total:
        return

    processes = getattr(settings, 'TENANT_PARALLEL_MIGRATION_MAX_PROCESSES', 2)
    chunks = getattr(settings, 'TENANT_PARALLEL_MIGRATION_CHUNKS', 2)

    from django.db import connection

    connection.close()
    connection.connection = None

    run_migrations_p = functools.partial(
        run_migrations,
        self.args,
        self.options,
        self.codename,
        allow_atomic=False,
    )
    pool = multiprocessing.Pool(processes=processes)
    try:
        completed = 0
        show_progress = _should_show_progress(self.options)
        for _ in pool.imap_unordered(run_migrations_p, tenants, chunks):
            completed += 1
            if show_progress:
                write_tenant_migration_progress(completed, total)
    finally:
        pool.close()
        pool.join()


parallel_module.ParallelExecutor.run_tenant_migrations = (
    run_tenant_migrations_with_progress_parallel
)
standard_module.StandardExecutor.run_tenant_migrations = (
    run_tenant_migrations_with_progress_standard
)
