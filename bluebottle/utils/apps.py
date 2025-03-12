from django.apps import AppConfig


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
        import bluebottle.utils.monkey_patch_object_not_found  # noqa
