#!/usr/bin/python

import os, glob, sys, getopt
from django.conf import settings
from django.template import Context, Template, loader
from django.utils.translation import ugettext
from django.contrib.auth.models import AbstractBaseUser
import templatetag_handlebars
import re

from BeautifulSoup import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.normpath(os.path.join(__file__, '..', '..')))
USE_EMBER_STYLE_ATTRS=True
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates')
)

settings.configure(
    INSTALLED_APPS=('bluebottle.common','templatetag_handlebars','django.contrib.staticfiles','statici18n',),
    STATIC_URL='',
    ROOT_URLCONF='bluebottle.urls',
    AUTH_USER_MODEL='models.AbstractBaseUser'
)

def main(argv):
    destdir = './test/js/templates'
    try:
        opts, args = getopt.getopt(argv,"hd:",["destdir="])
    except getopt.GetoptError:
        print 'parse_templates.py -d <destdirectory>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'parse_templates.py -d <destdirectory>'
            sys.exit()
        elif opt in ("-d", "--destdir"):
            destdir = arg

    # Template method was returning an empty string if there was a comment (<!--..-->)
    #  => strip them out before passing to Template below
    pattern = '\<![ \r\n\t]*(--([^\-]|[\r\n]|-[^\-])*--[ \r\n\t]*)\>'
    htmlcomments = re.compile(pattern, re.DOTALL)

    munged_templates = ''
    for root, dirs, files in os.walk("bluebottle"):
        for file in files:
            if file.endswith(".hbs"):
                template_file = open(os.path.join(root, file), 'r')
                template = Template(htmlcomments.sub('', template_file.read()))
                munged_templates += template.render(Context({}))
                template_file.close()

    soup = BeautifulSoup(munged_templates)

    print('Templates written:')
    for tag in soup('script'):
        file = '%s/%s.handlebars' % (destdir, tag["id"].replace('/', '_'))
        f = open(file, 'w')
        f.write(tag.string.encode('utf-8').strip())
        f.close()
        print('   %s' % (file))

if __name__ == "__main__":
   main(sys.argv[1:])