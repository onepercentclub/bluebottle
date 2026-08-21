import re
import subprocess
from collections import Counter
from multiprocessing import Pool
from optparse import make_option

from bluebottle.clients.models import Client
from bluebottle.common.management.commands.base import Command as BaseCommand

# How many trailing log lines to show when a tenant fails.
ERROR_TAIL_LINES = 40


def reindex(schema_name, rebuild=False):
    """Reindex a tenant. If rebuild=False, use --populate to update in place."""
    mode = 'rebuild' if rebuild else 'populate'
    print(f'reindexing tenant {schema_name} ({mode})')
    if rebuild:
        cmd = [
            './manage.py', 'tenant_command', '-s', schema_name,
            'search_index', '--rebuild', '-f',
        ]
    else:
        cmd = [
            './manage.py', 'tenant_command', '-s', schema_name,
            'search_index', '--populate', '--refresh',
        ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return (schema_name, result.returncode, result.stdout or '')


def _summarize_bulk_index_errors(output):
    """
    BulkIndexError dumps every failed doc; pull unique ES rejection reasons.
    """
    reasons = Counter()
    for match in re.finditer(
        r"'type':\s*'([^']+)'[^]]*?'reason':\s*'((?:\\'|[^'])*)'",
        output,
        flags=re.DOTALL,
    ):
        error_type, reason = match.group(1), match.group(2).replace("\\'", "'")
        if error_type in {
            'document_parsing_exception',
            'mapper_parsing_exception',
            'illegal_argument_exception',
            'strict_dynamic_mapping_exception',
        } or 'failed to parse' in reason or 'mapper' in error_type:
            reasons[(error_type, reason[:300])] += 1

    if not reasons:
        for line in output.splitlines():
            if 'mapper_parsing_exception' in line or 'failed to parse field' in line:
                reasons[('parse', line.strip()[:300])] += 1
    return reasons


def _print_failure(schema_name, output):
    print(f'Tenant failed to index: {schema_name}')

    reasons = _summarize_bulk_index_errors(output or '')
    if reasons:
        print(f'--- unique Elasticsearch errors for {schema_name} ---')
        for (error_type, reason), count in reasons.most_common(10):
            print(f'  [{count}x] {error_type}: {reason}')
        print(f'--- end errors {schema_name} ---')
        print(
            'Hint: mapping conflicts usually need '
            f'`./manage.py reindex -s {schema_name} --rebuild`'
        )
        return

    lines = (output or '').rstrip().splitlines()
    tail = lines[-ERROR_TAIL_LINES:] if lines else ['(no output captured)']
    print(f'--- last {len(tail)} lines for {schema_name} ---')
    print('\n'.join(tail))
    print(f'--- end {schema_name} ---')


class Command(BaseCommand):
    help = (
        'Reindex all tenants. By default uses --populate (update in place without '
        'dropping the index). Use --rebuild to recreate indices from scratch.'
    )

    option_list = BaseCommand.options + (
        make_option(
            '--processes',
            default=8,
            help='How many processes run in parallel'
        ),
        make_option(
            '-s',
            default=None,
            help='Only run for specified tenant schema'
        ),
        make_option(
            '--rebuild',
            action='store_true',
            default=False,
            help='Drop and recreate indices (full rebuild). Default is populate-only.'
        ),
    )

    def handle(self, *args, **options):
        tenant_schema = options['s']
        rebuild = options['rebuild']
        if tenant_schema:
            tenant, result, output = reindex(str(tenant_schema), rebuild=rebuild)
            if result != 0:
                _print_failure(tenant, output)
            elif output:
                print(output.rstrip())
        else:
            processes = int(options.get('processes', 8))
            pool = Pool(processes=processes)
            tasks = [
                pool.apply_async(
                    reindex,
                    args=[str(tenant.schema_name)],
                    kwds={'rebuild': rebuild},
                )
                for tenant in Client.objects.all()
            ]
            results = [result.get() for result in tasks]
            for tenant, result, output in results:
                if result != 0:
                    _print_failure(tenant, output)
            pool.close()
