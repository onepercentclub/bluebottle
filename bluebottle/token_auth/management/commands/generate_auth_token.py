from optparse import make_option

from django.core.management.base import BaseCommand
from bluebottle.token_auth.auth.booking import generate_token

try:
    from django.utils.six.moves import input
except ImportError:
    input = raw_input


class Command(BaseCommand):
    help = "Generate a authentication token"

    def __init__(self):
        self.option_list = self.option_list + (
            make_option('--email', '-e', dest='email', default=None,
                        help="Email to generate a token for."),
            make_option('--first-name', '-f', dest='first-name', default=None,
                        help="Last name for the user."),
            make_option('--last-name', '-l', dest='last-name', default=None,
                        help="First name for the user."),
        )

        super(Command, self).__init__()

    def handle(self, *args, **options):
        if options.get('email'):
            email = options['email']
        else:
            email = None
            while not email:
                email = input("Enter email address: ")

        if options.get('first-name'):
            first_name = options['first-name']
        else:
            default = email.split('@')[0].title()
            first_name = input("Enter first name ({0}): ".format(default)) or default

        if options.get('last-name'):
            last_name = options['last-name']
        else:
            default = email.split('@')[1].split('.')[0].title()
            last_name = input("Enter last name ({0}): ".format(default)) or default

        if options.get('username'):
            username = options['username']
        else:
            default = email.split('@')[0]
            username = input("Enter username ({0}): ".format(default)) or default

        token = generate_token(email=email, username=username,
                               first_name=first_name, last_name=last_name)
        self.stdout.write('Token:  {0}'.format(token))
