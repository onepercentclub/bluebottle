from django.db import models
from django.db.models.fields.related import ForeignKey
from django.forms import ModelChoiceField

from bluebottle.files.widgets import ImageWidget, DocumentWidget, PrivateDocumentWidget


class ImageField(ForeignKey):

    def __init__(self, to=None, on_delete=models.CASCADE, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):
        if not to:
            from bluebottle.files.models import Image
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

    def __init__(self, to=None, on_delete=models.CASCADE, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):
        if not to:
            from bluebottle.files.models import Document
            to = Document
        super(DocumentField, self).__init__(
            to, on_delete, related_name, related_query_name,
            limit_choices_to, parent_link, to_field,
            db_constraint, **kwargs
        )

    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        queryset = self.remote_field.model._default_manager.using(db)
        defaults = {
            'widget': DocumentWidget,
            'form_class': ModelChoiceField,
            'queryset': queryset,
            'to_field_name': self.remote_field.field_name,
        }
        defaults.update(kwargs)
        return super(DocumentField, self).formfield(**defaults)


class PrivateDocumentModelChoiceField(ModelChoiceField):
    def __init__(self, related_field=None, view_name=None, *args, **kwargs):
        self.related_field = related_field
        self.view_name = view_name
        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        attrs['related_field'] = self.related_field
        attrs['view_name'] = self.view_name

        return attrs


class PrivateDocumentField(ForeignKey):

    def __init__(self, to=None, on_delete=models.CASCADE, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, view_name=None, **kwargs):
        if not to:
            from bluebottle.files.models import PrivateDocument
            to = PrivateDocument

        self.view_name = view_name

        super(PrivateDocumentField, self).__init__(
            to, on_delete, related_name, related_query_name,
            limit_choices_to, parent_link, to_field,
            db_constraint, **kwargs
        )

    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        queryset = self.remote_field.model._default_manager.using(db)
        defaults = {
            'widget': PrivateDocumentWidget,
            'related_field': self.related_query_name(),
            'view_name': self.view_name,
            'form_class': PrivateDocumentModelChoiceField,
            'queryset': queryset,
            'to_field_name': self.remote_field.field_name,
        }
        kwargs.update(defaults)
        return super(PrivateDocumentField, self).formfield(**kwargs)
