#!/usr/bin/env python3

import sys
import os
import argparse

import polib

display_missing = 10

parser = argparse.ArgumentParser(description='Check translation percentages')

# Optional argument
parser.add_argument(
    '--source-locale',
    type=str,
    default='en',
    help='Base locale to check strings against'
)

parser.add_argument(
    'path',
    nargs="?",
    type=str,
    default=os.path.join(os.getcwd(), 'locale/'),
    help='Path to locale files'
)

parser.add_argument(
    '--locales',
    type=str,
    default='nl',
    help='Locales to check'
)

parser.add_argument(
    '--no-fail',
    action='store_true',
    help='Do not exit with code 1 when translations are missing (report only)'
)


if __name__ == '__main__':
    args = parser.parse_args()

    failed = False

    languages = [
        lang for lang in os.listdir(args.path)
        if os.path.isdir(os.path.join(args.path, lang)) and lang != args.source_locale
    ]
    sources = polib.pofile(os.path.join(args.path, args.source_locale, 'LC_MESSAGES/django.po'))

    for locale in args.locales.split(','):
        path = os.path.join(args.path, locale, 'LC_MESSAGES/django.po')
        translations = polib.pofile(path)

        missing = []
        for source in sources:
            message = translations.find(source.msgid)

            if not message or not message.translated():
                missing.append(source.msgid)

        if missing:
            failed = True
            print(f'Missing translations for {locale}\n')

            for trans in missing[:display_missing]:
                print(f'* {trans.strip()}\n')

            if len(missing) > display_missing:
                print(f'and {len(missing) - display_missing} more\n')
        else:
            print(f'All strings for {locale} are translated\n')

    if failed and not args.no_fail:
        sys.exit(1)
