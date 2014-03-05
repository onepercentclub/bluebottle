from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.contrib.contenttypes.management import update_all_contenttypes, update_contenttypes
from optparse import make_option

'''
    The following command allow you to easily manage the Content Type of the project

    - Delete the content types for a single model or for app_label:
        [--delete-model; --delete-label]

    - Delete content types for obsolete applications:
        [--delete-obsolete]

    - Update content types for a single application:
        [--uS, --update-single]

    - Update content types for all the applications:
        [--uA, --update-all]

    - Show the content types:
        [-s, --show]    #all
        [--in]          #shows the ones in INSTALLED_APPS
        [--out]         #shows the ones not in INSTALLED_APPS
'''

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--delete-model', metavar='ct',
                    dest='deleteModel', default=False,
                    help='Delete the contenttypes for the specified model'
                    ),

        make_option('--delete-label', metavar='ct',
                    dest='deleteLabel', default=False,
                    help='Delete the contenttypes for the specified app,'
                    ),

        make_option('--delete-obsolete', action='store_true',
                    dest='deleteObsolete', default=False,
                    help='Delete all the content types for old application,'
                         'remove any model which has no reference (app_label) in the INSTALLED_APP'
                    ),

        make_option('--uS', '--update-single', metavar='ct',
                    dest='updateSingle', default=False,
                    help='Creates content types for models in the given app, '
                         'removing any model' \
                         'entries that no longer have a matching model class'
                    ),

        make_option('--uA', '--update-all', action='store_true',
                    dest='updateAll', default=False,
                    help='Creates content types for models in all the installed app, '
                         'removing any model entries that no longer have a matching model class'
                    ),

        make_option('-s', '--show', action='store_true',
                    dest='show', default=False,
                    help='Return the list of all the ContentTypes ordered by model'
                    ),

        make_option('--in', action='store_true',
                    dest='showIn', default=False,
                    help="used with show: shows contentTypes related to apps in INSTALLED_APPS"
                    ),

        make_option('--out', action='store_true',
                    dest='showOut', default=False,
                    help="used with show: shows contentTypes not related to apps in INSTALLED_APPS"
                    ),
    )

    def handle(self, *args, **options):

        if options['deleteModel']:
            modelToDelete = options['deleteModel']
            self.stdout.write("Going to delete the contenttype for the %s model" %modelToDelete)
            ContentType.objects.filter(model=modelToDelete).delete()

        if options['deleteLabel']:
            labelToDelete = options['deleteLabel']
            self.stdout.write("Going to delete the contenttypes for the '%s' app" %labelToDelete)
            ContentType.objects.filter(app_label=labelToDelete).delete()

        if options['deleteObsolete']:
            self.stdout.write("Going to Deleted all obsolete ContentType")
            for ct in ContentType.objects.exclude(app_label__in=settings.INSTALLED_APPS):
                self.stdout.write("Deleting %s" %ct.model)
                ct.delete()

        if options['updateSingle']:
            contentToUpdate = options['updateSingle']
            self.stdout.write("Going to Update the content type for the models "
                              "in the %s app" %contentToUpdate)
            update_contenttypes(contentToUpdate)

        if options['updateAll']:
            self.stdout.write("Going to Update the content type for all the apps")
            update_all_contenttypes()

        if options['show']:

            queryset = ContentType.objects.all()
            if options['showIn']:
                queryset = ContentType.objects.filter(app_label__in=settings.INSTALLED_APPS)
            elif options['showOut']:
                queryset = ContentType.objects.exclude(app_label__in=settings.INSTALLED_APPS)

            self.stdout.write("Here is the list of contenttypes ordered per app_label: ")
            self.stdout.write("\n")
            app = []
            modelCounter = 0
            labelCounter = 0
            for content in queryset:
                if content.app_label in app:
                    self.stdout.write('    - %s'%content.model)
                    modelCounter += 1
                else:
                    app.append(content.app_label)
                    self.stdout.write('- %s'%content.app_label)
                    self.stdout.write('    - %s'%content.model)
                    labelCounter += 1
                    modelCounter += 1
            self.stdout.write("\n")
            self.stdout.write("%s of apps" %labelCounter)
            self.stdout.write("%s of models" %modelCounter)

        self.stdout.write("Done")