import os
import yaml

from django.conf import settings
from django.core.management.base import BaseCommand

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client

from bluebottle.projects.models import Project, ProjectPhaseLog
from bluebottle.tasks.models import Task, TaskMember


class Command(BaseCommand):
    help = 'Create report views (database)'

    def add_arguments(self, parser):
        parser.add_argument('--skip', '-s', action='store', dest='skip',
                            help="File path to sql for creating report views")
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="Tenant name")

    def generate_fixtures(self, client_name, skip=50):
        client = Client.objects.get(client_name=client_name)
        results = {
            'members': [],
            'projects': [],
        }

        print('Checking {} with skip of {}'.format(client_name, skip))

        def append_member(member):
            results['members'].append({
                'id': member.id,
                'first_name': member.first_name
            })

        with LocalTenant(client):
            # Get projects from 2017
            projects = Project.objects.filter(created__gt='2017-01-01 00:00:00+02',
                                              created__lte='2017-12-31 23:59:59+02')

            count = 0
            for project in projects:
                if count < skip:
                    count = count + 1
                    continue

                count = 0
                append_member(project.owner)
                tasks = []
                for task in Task.objects.filter(project=project):
                    append_member(task.author)
                    task_data = {
                        'id': task.id,
                        'title': task.title,
                        'status': str(task.status),
                        'deadline': task.deadline
                    }

                    taskmembers = []
                    for taskmember in TaskMember.objects.filter(task=task):
                        append_member(taskmember.member)
                        taskmembers.append({
                            'member_id': taskmember.member_id,
                            'time_spent': taskmember.time_spent
                        })

                    task_data['taskmembers'] = taskmembers
                    tasks.append(task_data)

                statuslog = []
                for log in ProjectPhaseLog.objects.filter(project=project):
                    statuslog.append({
                        'status': log.status.slug,
                        'start': log.start,
                    })

                results['projects'].append({
                    'id': project.id,
                    'title': project.title,
                    'user_id': project.owner_id,
                    'tasks': tasks,
                    'statuslog': statuslog
                })

            # Unique members
            results['members'] = [dict(y) for y in set(tuple(x.items()) for x in results['members'])]

            yaml_path = os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'analytics', 'tests',
                                     'files', 'report_fixtures.yml')
            with open(yaml_path, 'w') as f:
                yaml.dump(results, f, default_flow_style=False)

            print('Generated fixtures for {} members and {} projects'.format(len(results['members'])))

    def handle(self, *args, **options):
        if options['tenant']:
            client_name = options['tenant']
        else:
            raise Exception('`Please specify a tenant to use for the fixtures')

        skip = int(options['skip'])

        self.generate_fixtures(client_name, skip)
