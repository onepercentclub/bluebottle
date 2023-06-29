from django.apps import AppConfig

import bluebottle.utils.monkey_patch_summernote  # noqa


class UtilsConfig(AppConfig):
    name = 'bluebottle.utils'
    verbose_name = "Utils"

    def ready(self):
        import bluebottle.utils.monkey_patch_migration  # noqa
        import bluebottle.utils.monkey_patch_money_readonly_fields  # noqa
        import bluebottle.utils.monkey_patch_parler  # noqa
        import bluebottle.utils.monkey_patch_password_validators  # noqa
        import bluebottle.utils.monkey_patch_jet  # noqa
        import bluebottle.utils.monkey_patch_current_site  # noqa
