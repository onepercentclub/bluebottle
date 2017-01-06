# Borrowed from:
# https://github.com/celery/django-celery/blob/master/djcelery/management/base.py
# to allow option_list to work with Django 1.10+

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    options = ()

    if hasattr(BaseCommand, 'option_list'):
        options = BaseCommand.option_list
    else:
        def add_arguments(self, parser):
            option_typemap = {
                "string": str,
                "int": int,
                "float": float
            }
            for opt in self.option_list:
                option = {k: v for k, v in opt.__dict__.items() if v is not None}
                flags = (option.get("_long_opts", []) + option.get("_short_opts", []))
                if option.get('default') == ('NO', 'DEFAULT'):
                    option['default'] = None
                if option.get("nargs") == 1:
                    del option["nargs"]
                del option["_long_opts"]
                del option["_short_opts"]
                if "type" in option:
                    opttype = option["type"]
                    option["type"] = option_typemap.get(opttype, opttype)
                parser.add_argument(*flags, **option)

    @property
    def option_list(self):
        return [x for x in self.options]
