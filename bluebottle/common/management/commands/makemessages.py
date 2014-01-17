import glob
import re
import sys
import os

from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.core.management.commands.makemessages import handle_extensions, _popen, STATUS_OK, find_files, process_file, write_po_file
from django.utils.text import get_text_list


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--locale', '-l', default=None, dest='locale',
            help='Creates or updates the message files for the given locale (e.g. pt_BR).'),
        make_option('--domain', '-d', default='django', dest='domain',
            help='The domain of the message files (default: "django").'),
        make_option('--all', '-a', action='store_true', dest='all',
            default=False, help='Updates the message files for all existing locales.'),
        make_option('--extension', '-e', dest='extensions',
            help='The file extension(s) to examine (default: "html,txt", or "js" if the domain is "djangojs"). Separate multiple extensions with commas, or use -e multiple times.',
            action='append'),
        make_option('--symlinks', '-s', action='store_true', dest='symlinks',
            default=False, help='Follows symlinks to directories when examining source code and templates for translation strings.'),
        make_option('--ignore', '-i', action='append', dest='ignore_patterns',
            default=[], metavar='PATTERN', help='Ignore files or directories matching this glob-style pattern. Use multiple times to ignore more.'),
        make_option('--no-default-ignore', action='store_false', dest='use_default_ignore_patterns',
            default=True, help="Don't ignore the common glob-style patterns 'CVS', '.*' and '*~'."),
        make_option('--no-wrap', action='store_true', dest='no_wrap',
            default=False, help="Don't break long message lines into several lines"),
        make_option('--no-location', action='store_true', dest='no_location',
            default=False, help="Don't write '#: filename:line' lines"),
        make_option('--no-obsolete', action='store_true', dest='no_obsolete',
            default=False, help="Remove obsolete message strings"),
        make_option('--include', action='append', dest='include_paths', default=[], help="Include additional paths."),
    )
    help = ("Runs over the entire source tree of the current directory and "
"pulls out all strings marked for translation. It creates (or updates) a message "
"file in the conf/locale (in the django tree) or locale (for projects and "
"applications) directory.\n\nYou must run this command with one of either the "
"--locale or --all options.")

    requires_model_validation = False
    can_import_settings = False

    def handle_noargs(self, *args, **options):
        include_paths = options.get('include_paths')

        locale = options.get('locale')
        domain = options.get('domain')
        verbosity = int(options.get('verbosity'))
        process_all = options.get('all')
        extensions = options.get('extensions')
        symlinks = options.get('symlinks')
        ignore_patterns = options.get('ignore_patterns')
        if options.get('use_default_ignore_patterns'):
            ignore_patterns += ['CVS', '.*', '*~']
        ignore_patterns = list(set(ignore_patterns))
        no_wrap = options.get('no_wrap')
        no_location = options.get('no_location')
        no_obsolete = options.get('no_obsolete')

        if domain == 'djangojs':
            exts = extensions if extensions else ['js']
        else:
            exts = extensions if extensions else ['html', 'txt']
        extensions = handle_extensions(exts)

        if verbosity > 1:
            self.stdout.write('examining files with the extensions: %s\n'
                             % get_text_list(list(extensions), 'and'))

        make_messages(locale, domain, verbosity, process_all, extensions,
            symlinks, ignore_patterns, no_wrap, no_location, no_obsolete, self.stdout, include_paths)




def make_messages(locale=None, domain='django', verbosity=1, all=False,
        extensions=None, symlinks=False, ignore_patterns=None, no_wrap=False,
        no_location=False, no_obsolete=False, stdout=sys.stdout, include_paths=None):
    """
    Uses the ``locale/`` directory from the Django Git tree or an
    application/project to process all files with translatable literals for
    the :param domain: domain and :param locale: locale.
    """
    if include_paths is None:
        include_paths = []

    # Need to ensure that the i18n framework is enabled
    from django.conf import settings
    if settings.configured:
        settings.USE_I18N = True
    else:
        settings.configure(USE_I18N = True)

    if ignore_patterns is None:
        ignore_patterns = []

    invoked_for_django = False
    if os.path.isdir(os.path.join('conf', 'locale')):
        localedir = os.path.abspath(os.path.join('conf', 'locale'))
        invoked_for_django = True
        # Ignoring all contrib apps
        ignore_patterns += ['contrib/*']
    elif os.path.isdir('locale'):
        localedir = os.path.abspath('locale')
    else:
        raise CommandError("This script should be run from the Django Git "
                "tree or your project or app tree. If you did indeed run it "
                "from the Git checkout or your project or application, "
                "maybe you are just missing the conf/locale (in the django "
                "tree) or locale (for project and application) directory? It "
                "is not created automatically, you have to create it by hand "
                "if you want to enable i18n for your project or application.")

    if domain not in ('django', 'djangojs'):
        raise CommandError("currently makemessages only supports domains 'django' and 'djangojs'")

    if (locale is None and not all) or domain is None:
        message = "Type '%s help %s' for usage information." % (os.path.basename(sys.argv[0]), sys.argv[1])
        raise CommandError(message)

    # We require gettext version 0.15 or newer.
    output, errors, status = _popen('xgettext --version')
    if status != STATUS_OK:
        raise CommandError("Error running xgettext. Note that Django "
                    "internationalization requires GNU gettext 0.15 or newer.")
    match = re.search(r'(?P<major>\d+)\.(?P<minor>\d+)', output)
    if match:
        xversion = (int(match.group('major')), int(match.group('minor')))
        if xversion < (0, 15):
            raise CommandError("Django internationalization requires GNU "
                    "gettext 0.15 or newer. You are using version %s, please "
                    "upgrade your gettext toolset." % match.group())

    locales = []
    if locale is not None:
        locales.append(str(locale))
    elif all:
        locale_dirs = filter(os.path.isdir, glob.glob('%s/*' % localedir))
        locales = [os.path.basename(l) for l in locale_dirs]

    wrap = '--no-wrap' if no_wrap else ''
    location = '--no-location' if no_location else ''

    for locale in locales:
        if verbosity > 0:
            stdout.write("processing language %s\n" % locale)
        basedir = os.path.join(localedir, locale, 'LC_MESSAGES')
        if not os.path.isdir(basedir):
            os.makedirs(basedir)

        pofile = os.path.join(basedir, '%s.po' % str(domain))
        potfile = os.path.join(basedir, '%s.pot' % str(domain))

        if os.path.exists(potfile):
            os.unlink(potfile)

        for root in ['.'] + [os.path.abspath(r) for r in include_paths]:
            stdout.write('  processing directory: {0}'.format(root))
            for dirpath, file in find_files(root, ignore_patterns, verbosity,
                    stdout, symlinks=symlinks):
                try:
                    process_file(file, dirpath, potfile, domain, verbosity, extensions,
                            wrap, location, stdout)
                except UnicodeDecodeError:
                    stdout.write("UnicodeDecodeError: skipped file %s in %s" % (file, dirpath))

        if os.path.exists(potfile):
            write_po_file(pofile, potfile, domain, locale, verbosity, stdout,
                    not invoked_for_django, wrap, location, no_obsolete)
