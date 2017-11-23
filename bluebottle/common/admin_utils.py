from django.contrib import admin
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ManyToManyRawIdWidget, \
    ForeignKeyRawIdWidget
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.html import escape

"""
    Those modules are needed to make raw_id_fields (ForeignKeys, and ManyToManyFields)
    links which redirect to their change pages

    Ref:
        https://djangosnippets.org/snippets/2217/
        https://gist.github.com/EmilStenstrom/4761449 [usage]
"""


class VerboseForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(
                **{key: value})
            change_url = reverse(
                "admin:{0}_{1}_change".format(obj._meta.app_label,
                                              obj._meta.object_name.lower()),
                args=(obj.pk,)
            )
            return u'&nbsp;<strong><a href="{0}">{1}</a></strong>'.format(
                change_url, escape(obj))
        except (ValueError, self.rel.to.DoesNotExist):
            return '???'


class VerboseManyToManyRawIdWidget(ManyToManyRawIdWidget):
    def label_for_value(self, value):
        values = value.split(',')
        str_values = []
        key = self.rel.get_related_field().name
        for v in values:
            try:
                obj = self.rel.to._default_manager.using(self.db).get(
                    **{key: v})
                x = smart_unicode(obj)
                change_url = reverse(
                    "admin:{0}_{1}_change".format(obj._meta.app_label,
                                                  obj._meta.object_name.lower()),
                    args=(obj.pk,)
                )
                str_values += [
                    '<strong><a href="{0}">{1}</a></strong>'.format(change_url,
                                                                    escape(x))]
            except self.rel.to.DoesNotExist:
                str_values += [u'???']
        return u', '.join(str_values)


class ImprovedModelForm(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs.pop("request", None)
            type = db_field.rel.__class__.__name__
            if type == "ManyToOneRel":
                kwargs['widget'] = VerboseForeignKeyRawIdWidget(db_field.rel,
                                                                site)
            elif type == "ManyToManyRel":
                kwargs['widget'] = VerboseManyToManyRawIdWidget(db_field.rel,
                                                                site)
            return db_field.formfield(**kwargs)
        return super(ImprovedModelForm, self).formfield_for_dbfield(db_field,
                                                                    **kwargs)
