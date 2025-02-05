#!/usr/bin/env python3

import os
import argparse

import polib

display_missing = 3

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
    'locales',
    nargs="?",
    type=str,
    default='nl',
    help='Locales to check'
)


if __name__ == '__main__':
    args = parser.parse_args()

    languages = [
        lang for lang in os.listdir(args.path)
        if os.path.isdir(os.path.join(args.path, lang)) and lang != args.source_locale
    ]
    sources = polib.pofile(os.path.join(args.path, args.source_locale, 'LC_MESSAGES/django.po'))


    for locale in args.locales.split(','):
        path = os.path.join(args.path, locale,  'LC_MESSAGES/django.po')
        print(path)
        translations = polib.pofile(path)

        missing = []
        for source in sources:
            message = translations.find(source.msgid)

            if not message or not message.translated():
                missing.append(source.msgid)

        if missing:
            print(f'Missing translatoins for {locale}\n')

            for trans in missing[:display_missing]:
                print(f'* {trans.strip()}\n')

            if len(missing) > 3:
                print(f'and {len(missing) - display_missing} more\n')
        else:
            print(f'All strings for {locale} are translated\n')
