import string
import random
import os
import requests
import json
import getpass

from django.utils.encoding import force_str
from django.conf import settings
from django.template.loader import render_to_string
from django.core.management import call_command
from optparse import make_option
from tenant_extras.management.commands.makepo import Command as BaseCommand


class Command(BaseCommand):
    help = 'Post setup for create a tenant'
    base_url = "https://www.transifex.com/api/2/"

    def add_arguments(self, parser):
        parser.add_argument('--client-name',
                    help='Specifies the client name for the tenant \
                    (e.g. "new-tenant").')

    def handle(self, *args, **options):
        client_name = options.get('client_name', None)

        client_name.replace('_', '-')

        if client_name:
            self.create_client_file_structure(client_name)
            self.create_properties_file(client_name)
            self.create_tx_config_file(client_name)
            self.create_transifex_repo(client_name)
            self.generate_push_api_translations(client_name)

        self.stdout.write("Don't forget to update the ALLOWED_HOSTS setting in the server_prod and server_stage settings files to include your new tenant domain")

    def generate_push_api_translations(self, client_name):
        call_command('txtranslate',
                     pocmd='makepo_ext',
                     push=True,
                     tenant='{0}'.format(client_name))

    def create_transifex_repo(self, client_name):
        username = None
        password = None

        while username is None:
            if not username:
                input_msg = "Please give your Transifex username"
                username = raw_input(force_str('%s: ' % input_msg))

        while password is None:
            if not password:
                input_msg = "Please give your Transifex password"
                password = getpass.getpass(force_str('%s: ' % input_msg))

        projects_url = self.base_url + 'projects/'

        name = slug = "reef-{0}".format(client_name)

        headers = {'content-type': 'application/json'}

        payload = {'name': name,
                   'slug': slug,
                   'description': "",
                   #'team': 'OnePercentClub', Field is broken at Transifex
                   'source_language_code': 'en',
                   'private': 'True'}

        self.stdout.write("Creating Transifex repo")
        res = requests.post(projects_url,
                            auth=(username, password),
                            data=json.dumps(payload),
                            headers=headers)

        if res.status_code == 201:
            self.stdout.write("Client Transifex repo created")
            self.create_languages(slug, username, password)
        else:
            self.stdout.write("Error creating Transifex repo")
            self.stdout.write('Code: {0}, {1}'.format(res.status_code,
                                                      res.content))

    def create_languages(self, project_slug, username, password):
        languages_url = self.base_url + 'project/' + project_slug + '/languages/'

        headers = {'content-type': 'application/json'}

        # TODO: languages should be a question for the user when running the command.
        languages = ['en_GB', 'nl']

        coordinators = ['devteam_onepercent', 'aethemba', 'rollick', 'gannetson',
                        'ernst.odolphi', 'iivvoo', 'johnm', 'sezayi', 'SvenDekker',
                        ]

        for language in languages:
            payload = {'language_code': language,
                       'coordinators': coordinators}

            self.stdout.write("Adding language {0}".format(language))

            res = requests.post(languages_url,
                                auth=(username, password),
                                data=json.dumps(payload),
                                headers=headers)

            if res.status_code == 201:
                self.stdout.write("Added language {0}".format(language))

    def create_client_file_structure(self, client_name):
        """ Create the bare directory structure for a tenant """
        tenant_dir = ''.join([getattr(settings, 'MULTI_TENANT_DIR', None),
                             '/', client_name])

        tx_dir = "/.tx/"
        new_path = tenant_dir + tx_dir
        if not os.path.exists(new_path):
            os.makedirs(new_path)

        return True

    def get_properties_information(self, client_name):

        default_project_type = 'sourcing'
        default_contact_email = 'info@{0}.com'.format(client_name)
        default_country_code = 'NL'
        default_english = 'yes'
        default_dutch = 'yes'
        default_recurring_donations = 'no'
        default_maps = 'AIzaSyCsUbYPmNR84nin7GWy-hJ-jnZQO1g70SA'
        default_mail_sender = 'info@{0}.com'.format(client_name)
        default_mail_website = 'www.{0}.com'.format(client_name)
        default_date_format = 'l'

        info = {'project_type': '',
                'contact_email': '',
                'country_code': '',
                'languages': {'en': '',
                              'nl': ''},
                'language_code': '',
                'mixpanel': '',
                'maps': '',
                'recurring_donations': '',
                'mail_sender': '',
                'mail_address': '',
                'mail_footer': '',
                'mail_website': '',
                'client_name': client_name,
                'date_format': ''}

        self.stdout.write("\n\n")
        self.stdout.write("General tenant information")
        self.stdout.write("\n")

        while info['project_type'] is '':
            input_msg = "Project type? ['funding', 'sourcing', 'both']"
            input_msg = "%s (leave blank to use '%s')" % (input_msg,
                                                          default_project_type)
            user_input = raw_input(force_str('%s: ' % input_msg)) or default_project_type

            if user_input in ['funding', 'sourcing', 'both']:
                if user_input == 'funding' or user_input == 'both':
                    raw_input('Ask more payment details here')
                    info['project_type'] = user_input
                else:
                    info['project_type'] = user_input
            else:
                input(force_str("Please specify 'funding', 'sourcing' or 'both':"))

        input_msg = "Contact email?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_contact_email)
        info['contact_email'] = raw_input(force_str('%s: ' % input_msg)) or default_contact_email

        self.stdout.write("\n\n")
        self.stdout.write("Tenant email information")
        self.stdout.write("\n")

        input_msg = "From e-email used in tenant mail?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_mail_sender)
        info['mail_sender'] = raw_input(force_str('%s: ' % input_msg)) or default_mail_sender

        while info['mail_address'] is '':
            input_msg = "Address in tenant email?"
            info['mail_address'] = raw_input(force_str('%s: ' % input_msg))

        while info['mail_footer'] is '':
            input_msg = "Footer text in tenant email?"
            info['mail_footer'] = raw_input(force_str('%s: ' % input_msg))

        input_msg = "Website link in tenant email?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_mail_website)
        info['mail_website'] = raw_input(force_str('%s: ' % input_msg)) or default_mail_website

        self.stdout.write("\n\n")
        self.stdout.write("Tenant language information")
        self.stdout.write("\n")

        input_msg = "Use English?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_english)
        user_input = raw_input(force_str('%s: ' % input_msg))
        if user_input.lower() in ['n', 'no']:
            info['languages']['en'] = False
        else:
            info['languages']['en'] = True

        input_msg = "Use Dutch?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_dutch)
        user_input = raw_input(force_str('%s: ' % input_msg))
        if user_input.lower() in ['n', 'no']:
            info['languages']['nl'] = False
        else:
            info['languages']['nl'] = True

        input_msg = "Default country code?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_country_code)
        user_input = raw_input(force_str('%s: ' % input_msg)) or default_country_code
        info['country_code'] = user_input.upper()
        info['language_code'] = user_input.lower()

        self.stdout.write("\n\n")
        self.stdout.write("Tenant feature information")
        self.stdout.write("\n")

        input_msg = "Use recurring donations?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_recurring_donations)
        user_input = raw_input(force_str('%s: ' % input_msg)) or default_recurring_donations

        info['recurring_donations'] = user_input.lower() in ['yes', 'y']

        input_msg = "Google Maps API key?"
        input_msg = "%s (leave blank to use %s)" % (input_msg, default_maps)
        info['maps'] = raw_input(force_str('%s: ' % input_msg)) or default_maps

        input_msg = "Does this tenant prefer a specific date format?"
        input_msg = "%s (leave blank to use '%s')" % (input_msg, default_date_format)
        user_input = raw_input(force_str('%s: ' % input_msg))

        info['date_format'] = user_input or default_date_format

        return info

    def create_properties_file(self, client_name):
        """ Write a properties.py file for the tenant """
        info = self.get_properties_information(client_name)

        info.update({'jwt_secret': self.generate_jwt_key()})

        string = render_to_string('create_tenant_setup/properties.tpl', info)

        properties_path = ''.join([getattr(settings, 'MULTI_TENANT_DIR', None),
                                  '/', client_name, '/properties.py'])

        overwrite = False
        if os.path.exists(properties_path):
            user_input = raw_input("Overwrite existing properties file? y/N")
            if user_input in ['yes', 'y', 'Y']:
                overwrite = True

        if overwrite or not os.path.exists(properties_path):
            with open(properties_path, "w") as properties_file:
                properties_file.write(string)

    def generate_jwt_key(self):
        """ Generate a 50 char random key"""
        return ''.join(random.choice(string.ascii_uppercase +
                                     string.digits +
                                     string.ascii_lowercase) for _ in range(50))

    def create_tx_config_file(self, client_name):
        """ Create a tenant-specific tx-config file """

        string = render_to_string('create_tenant_setup/txconfig.tpl',
                                  {'client_name': client_name})

        config_path = ''.join([getattr(settings, 'MULTI_TENANT_DIR', None),
                              '/', client_name, '/.tx/config'])

        with open(config_path, "w") as config_file:
            config_file.write(string)
