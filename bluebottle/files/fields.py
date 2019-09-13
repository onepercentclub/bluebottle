from django.db.models.fields.related import ForeignKey
from django.forms import ModelChoiceField

from bluebottle.files.models import Image
from bluebottle.files.widgets import ImageWidget


class ImageField(ForeignKey):

    def __init__(self, to=None, on_delete=None, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):
        if not to:
            to = Image
        super(ImageField, self).__init__(
            to, on_delete, related_name, related_query_name,
            limit_choices_to, parent_link, to_field,
            db_constraint, **kwargs
        )

    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        queryset = self.remote_field.model._default_manager.using(db)
        defaults = {
            'widget': ImageWidget,
            'form_class': ModelChoiceField,
            'queryset': queryset,
            'to_field_name': self.remote_field.field_name,
        }
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)


class DocumentField(ForeignKey):

    def __init__(self, to=None, on_delete=None, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):
        if not to:
            to = Image
        super(DocumentField, self).__init__(
            to, on_delete, related_name, related_query_name,
            limit_choices_to, parent_link, to_field,
            db_constraint, **kwargs
        )

    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        queryset = self.remote_field.model._default_manager.using(db)
        defaults = {
            'widget': ImageWidget,
            'form_class': ModelChoiceField,
            'queryset': queryset,
            'to_field_name': self.remote_field.field_name,
        }
        defaults.update(kwargs)
        return super(DocumentField, self).formfield(**defaults)
