import fnmatch
import glob
import re
import sys
import os

from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.core.management.commands.makemessages import handle_extensions, \
    _popen, STATUS_OK, process_file, \
    write_po_file, is_ignored, Command as OriginalCommand
from django.utils.text import get_text_list


class Command(OriginalCommand):
    option_list = OriginalCommand.option_list + (
        make_option('--include', action='append', dest='include_paths',
                    default=[], help="Include additional paths."),
    )

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
                      symlinks, ignore_patterns, no_wrap, no_location,
                      no_obsolete, self.stdout, include_paths)


def find_files(root, ignore_patterns, verbosity, stdout=sys.stdout,
               symlinks=False):
    """
    Helper function to get all files in the given root.

    NOTE: An exact copy of the original function, however, it calls a local ``is_ignored`` function.
    NOTE: There seems to be a bug here in the original function as well, since root/subdir/.example (so, ignore pattern
    inside subdirectories) is not ignored either.
    """
    dir_suffix = '%s*' % os.sep
    norm_patterns = [p[:-len(dir_suffix)] if p.endswith(dir_suffix) else p for p
                     in ignore_patterns]
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True,
                                                followlinks=symlinks):
        for dirname in dirnames[:]:
            # NOTE: This line was changed, also affecting default behaviour.
            if is_ignored(dirname, norm_patterns):
                dirnames.remove(dirname)
                if verbosity > 1:
                    stdout.write('ignoring directory %s\n' % dirname)
        for filename in filenames:
            # NOTE: This line was changed, also affecting default behaviour.
            if is_ignored(filename, ignore_patterns):
                if verbosity > 1:
                    stdout.write(
                        'ignoring file %s in %s\n' % (filename, dirpath))
            else:
                all_files.extend([(dirpath, filename)])
    all_files.sort()
    return all_files


def make_messages(locale=None, domain='django', verbosity=1, all=False,
                  extensions=None, symlinks=False, ignore_patterns=None,
                  no_wrap=False,
                  no_location=False, no_obsolete=False, stdout=sys.stdout,
                  include_paths=None):
    """
    Uses the ``locale/`` directory from the Django Git tree or an
    application/project to process all files with translatable literals for
    the :param domain: domain and :param locale: locale.

    NOTE: Only a small part is changed to work with included files.
    """
    if include_paths is None:
        include_paths = []

    # Need to ensure that the i18n framework is enabled
    from django.conf import settings

    if settings.configured:
        settings.USE_I18N = True
    else:
        settings.configure(USE_I18N=True)

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
        raise CommandError(
            "currently makemessages only supports domains 'django' and 'djangojs'")

    if (locale is None and not all) or domain is None:
        message = "Type '%s help %s' for usage information." % (
        os.path.basename(sys.argv[0]), sys.argv[1])
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

        # NOTE: Additional for-loop added compared to original command to iterate over included projects.
        for root in ['.'] + include_paths:
            if not os.path.exists(root):
                stdout.write(
                    '  skipping directory: {0} (not found)'.format(root))
            else:
                stdout.write('  processing directory: {0}'.format(root))
                for dirpath, file in find_files(root, ignore_patterns,
                                                verbosity,
                                                stdout, symlinks=symlinks):
                    try:
                        process_file(file, dirpath, potfile, domain, verbosity,
                                     extensions,
                                     wrap, location, stdout)
                    except UnicodeDecodeError:
                        stdout.write(
                            "UnicodeDecodeError: skipped file %s in %s" % (
                            file, dirpath))

        if os.path.exists(potfile):
            write_po_file(pofile, potfile, domain, locale, verbosity, stdout,
                          not invoked_for_django, wrap, location, no_obsolete)
