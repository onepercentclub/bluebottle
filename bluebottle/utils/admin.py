import csv
from moneyed import Money
import urllib

from adminfilters.multiselect import UnionFieldListFilter
from django_singleton_admin.admin import SingletonAdmin

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.db.models.fields.files import FieldFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls.exceptions import NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.clients import properties
from bluebottle.members.models import Member, CustomMemberFieldSettings, CustomMemberField
from bluebottle.projects.models import CustomProjectFieldSettings, Project, CustomProjectField
from bluebottle.tasks.models import TaskMember
from bluebottle.utils.exchange_rates import convert

from .models import Language


def link_to(value, url_name, view_args=(), view_kwargs={}, query={},
            short_description=None, truncate=None):
    """
    Return admin field with link to named view with view_args/view_kwargs
    or view_[kw]args(obj) methods and HTTP GET parameters.

    Parameters:

      * value: function(object) or string for object proeprty name
      * url_name: name used to reverse() view
      * view_args: () or function(object) -> () returing view params
      * view_kwargs: {} or function(object) -> {} returing view params
      * query: {} or function(object) -> {} returning HTTP GET params
      * short_description: string with description, defaults to
        'value'/property name
    """

    def prop(self, obj):
        # Replace view_args methods by result of function calls
        if callable(view_args):
            args = view_args(obj)
        else:
            args = view_args

        if callable(view_kwargs):
            kwargs = view_kwargs(obj)
        else:
            kwargs = view_kwargs

        # Construct URL
        try:
            url = reverse(url_name, args=args, kwargs=kwargs)
        except NoReverseMatch:
            url = ''

        if callable(query):
            params = query(obj)
        else:
            params = query

        # Append query parameters
        if params:
            url += '?' + urllib.urlencode(params)

        # Get value
        if callable(value):
            # Call value getter
            new_value = value(obj)
        else:
            # String, assume object property
            assert isinstance(value, basestring)
            new_value = getattr(obj, value)

        if truncate:
            new_value = unicode(new_value)
            new_value = (new_value[:truncate] + '...') if len(
                new_value) > truncate else new_value

        if url and new_value:
            return format_html(
                u'<a href="{}">{}</a>',
                url, new_value
            )
        if url:
            return None
        return new_value

    if not short_description:
        # No short_description set, use property name
        assert isinstance(value, basestring)
        short_description = value
    prop.short_description = short_description

    return prop


class LanguageAdmin(admin.ModelAdmin):
    model = Language
    list_display = ('code', 'language_name', 'native_name')


admin.site.register(Language, LanguageAdmin)


def prep_field(request, obj, field, manyToManySep=';'):
    """ Returns the field as a unicode string. If the field is a callable, it
    attempts to call it first, without arguments.
    """
    if '__' in field:
        bits = field.split('__')
        field = bits.pop()

        for bit in bits:
            obj = getattr(obj, bit, None)

            if obj is None:
                return ""

    attr = getattr(obj, field)

    if isinstance(attr, (FieldFile,)):
        attr = request.build_absolute_uri(attr.url)

    output = attr() if callable(attr) else attr

    if isinstance(output, (list, tuple, QuerySet)):
        output = manyToManySep.join([str(item) for item in output])
    return unicode(output).encode('utf-8') if output else ""


def mark_as_plan_new(modeladmin, request, queryset):
    try:
        status = ProjectPhase.objects.get(slug='plan-new')
    except ProjectPhase.DoesNotExist:
        return
    queryset.update(status=status)


mark_as_plan_new.short_description = _("Mark selected projects as status Plan New")


def export_as_csv_action(description="Export as CSV", fields=None, exclude=None, header=True,
                         manyToManySep=';'):
    """ This function returns an export csv action. """

    def export_as_csv(modeladmin, request, queryset):
        """ Generic csv export admin action.
        Based on http://djangosnippets.org/snippets/2712/
        """
        opts = modeladmin.model._meta
        field_names = [field.name for field in opts.fields]
        labels = []

        if exclude:
            field_names = [f for f in field_names if f not in exclude]

        elif fields:
            try:
                field_names = [field for field, _ in fields]
                labels = [label for _, label in fields]
            except ValueError:
                field_names = [field for field in fields]
                labels = field_names

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            unicode(opts).replace('.', '_')
        )

        writer = csv.writer(response)

        if header:
            row = labels if labels else field_names
            # For project check if we have extra fields
            if queryset.model is Project:
                for field in CustomProjectFieldSettings.objects.all():
                    labels.append(field.name)
            if queryset.model is Member or queryset.model is TaskMember:
                for field in CustomMemberFieldSettings.objects.all():
                    labels.append(field.name)
            writer.writerow(row)

        for obj in queryset:
            row = [prep_field(request, obj, field, manyToManySep) for field in field_names]
            # Write extra field data
            if queryset.model is Project:
                for field in CustomProjectFieldSettings.objects.all():
                    try:
                        value = obj.extra.get(field=field).value
                    except CustomProjectField.DoesNotExist:
                        value = ''
                    row.append(value)
            if queryset.model is Member:
                for field in CustomMemberFieldSettings.objects.all():
                    try:
                        value = obj.extra.get(field=field).value
                    except CustomMemberField.DoesNotExist:
                        value = ''
                    row.append(value.encode('utf-8'))
            if queryset.model is TaskMember:
                for field in CustomMemberFieldSettings.objects.all():
                    try:
                        value = obj.member.extra.get(field=field).value
                    except CustomMemberField.DoesNotExist:
                        value = ''
                    row.append(value.encode('utf-8'))
            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    export_as_csv.acts_on_all = True
    return export_as_csv


class TotalAmountAdminChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        self.model_admin.change_list_template = 'utils/admin/total_amount_change_list.html'
        super(TotalAmountAdminChangeList, self).get_results(*args, **kwargs)

        total_column = self.model_admin.total_column or 'amount'
        currency_column = '{}_currency'.format(total_column)

        totals = self.queryset.values(
            currency_column
        ).annotate(
            total=Sum(total_column)
        ).order_by()

        amounts = [Money(total['total'], total[currency_column]) for total in totals]
        amounts = [convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts]
        self.total = sum(amounts) or Money(0, properties.DEFAULT_CURRENCY)


class LatLongMapPickerMixin(object):

    class Media:
        if hasattr(settings, 'MAPS_API_KEY') and settings.MAPS_API_KEY:
            css = {
                'all': ('css/admin/location_picker.css',),
            }
            js = (
                'https://maps.googleapis.com/maps/api/js?key={}'.format(settings.MAPS_API_KEY),
                'js/admin/location_picker.js',
            )


class BasePlatformSettingsAdmin(SingletonAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class TranslatedUnionFieldListFilter(UnionFieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(TranslatedUnionFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)
        # Remove duplicates and order by title
        self.lookup_choices = sorted(list(set(self.lookup_choices)), key=lambda tup: tup[1])


def log_action(obj, user, change_message='Changed', action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=unicode(obj),
        action_flag=action_flag,
        change_message=change_message
    )
