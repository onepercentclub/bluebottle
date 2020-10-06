from builtins import object


class HomePage(object):
    """ HomePage is a class to combine Slide, Quote and Stats into a single object.

    PermissionableModel requires a model_name and app_label to work with the
    ResourcePermissions class
    """
    def get(self, language):
        self.id = language
        return self

    class _meta(object):
        """ Properties `app_label` and `model_name` are present in django.models.model
        are required for ResourcePermissions to work.
        """
        app_label = 'homepage'
        model_name = 'homepage'
