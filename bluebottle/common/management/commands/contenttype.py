from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.contrib.contenttypes.management import update_all_contenttypes, update_contenttypes
from optparse import make_option

'''
    Cleaning ContentType
    options:
        update contenttype
        clean single contenttype
        clean all contenttypes
'''

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

        make_option('--delete-obsolete', action='store_true',
                    dest='deleteObsolete', default=False,
                    help='Delete all the content types for old application,'
                         'remove any model which has no reference in the INSTALLED_APP'
                    ),

        make_option('--uA', '--update-all', action='store_true',
                    dest='updateAll', default=False,
                    help='Creates content types for models in all the installed app, '
                         'removing any model entries that no longer have a matching model class.'
                    ),

        make_option('--uS', '--update-single', action='store_true',
                    dest='updateSingle', default=False,
                    help='Creates content types for models in the given app, '
                         'removing any model' \
                         'entries that no longer have a matching model class.'
                    ),

        make_option('-s', '--show', action='store_true',
                    dest='show', default=False,
                    help='Return the list of all the ContentTypes'),

        make_option('--in', action='store_true',
                    dest='showIn', default=False,
                    help="used with show: shows contentTypes related to apps in INSTALLED_APPS"),

        make_option('--out', action='store_true',
                    dest='showOut', default=False,
                    help="used with show: shows contentTypes not related to apps in INSTALLED_APPS"),

    )

    def handle(self, *args, **options):

        if options['deleteObsolete']:
            self.stdout.write("Going to Deleted all obsolete ContentType")
            for ct in ContentType.objects.exclude(app_label__in=settings.INSTALLED_APPS):
                self.stdout.write("Deleting %s FAKEMSG" %ct.model)
                ct.delete()
            self.stdout.write("Done")

        if options['updateSingle']:
            contentToBeDeleted = options['updateSingle']
            self.stdout.write("Going to Update the content type for the models "
                              "in the %s app" %contentToBeDeleted)
            update_contenttypes(contentToBeDeleted)
            self.stdout.write("Done")

        if options['updateAll']:
            self.stdout.write("Going to Update the content type for all the apps")
            update_all_contenttypes()
            self.stdout.write("Done")

        if options['show']:
            queryset_dict = {'all': ContentType.objects.all(),
                    'in': ContentType.objects.filter(app_label__in=settings.INSTALLED_APPS),
                    'out': ContentType.objects.exclude(app_label__in=settings.INSTALLED_APPS)}
            if options['showIn']:
                queryset = queryset_dict['in']
            if options['showOut']:
                queryset = queryset_dict['in']
            else:
                queryset = queryset_dict['all']

            self.stdout.write("here is the list ordered per app_label")
            app = []
            for content in queryset:
                if content.app_label in app:
                    self.stdout.write('    - %s'%content.model)
                else:
                    app.append(content.app_label)
                    self.stdout.write('- %s'%content.app_label)
                    self.stdout.write('    - %s'%content.model)