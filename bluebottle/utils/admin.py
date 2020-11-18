import csv
from builtins import str

import six
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.db.models.aggregates import Sum
from django.db.models.fields.files import FieldFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django_singleton_admin.admin import SingletonAdmin
from moneyed import Money
from parler.admin import TranslatableAdmin

from bluebottle.activities.models import Contribution
from bluebottle.clients import properties
from bluebottle.members.models import Member, CustomMemberFieldSettings, CustomMemberField
from bluebottle.utils.exchange_rates import convert
from .models import Language, TranslationPlatformSettings


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

    if isinstance(attr, FieldFile):
        attr = request.build_absolute_uri(attr.url)

    output = attr() if callable(attr) else attr

    if isinstance(output, (list, tuple, QuerySet)):
        output = manyToManySep.join([str(item) for item in output])
    return output if output else ""


def escape_csv_formulas(item):
    if item and isinstance(item, six.string_types):
        if item[0] in ['=', '+', '-', '@']:
            item = u"'" + item
        return smart_str(item)
    else:
        return item


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
            str(opts).replace('.', '_')
        )

        writer = csv.writer(response)

        if header:
            row = labels if labels else field_names
            if queryset.model is Member or issubclass(queryset.model, Contribution):
                for field in CustomMemberFieldSettings.objects.all():
                    labels.append(field.name)
            writer.writerow([escape_csv_formulas(item) for item in row])

        for obj in queryset:
            row = [prep_field(request, obj, field, manyToManySep) for field in field_names]

            # Write extra field data
            if queryset.model is Member:
                for field in CustomMemberFieldSettings.objects.all():
                    try:
                        value = obj.extra.get(field=field).value
                    except CustomMemberField.DoesNotExist:
                        value = ''
                    row.append(value)
            if isinstance(obj, Contribution):
                for field in CustomMemberFieldSettings.objects.all():
                    try:
                        value = obj.user.extra.get(field=field).value
                    except CustomMemberField.DoesNotExist:
                        value = ''
                    row.append(value)
            escaped_row = [escape_csv_formulas(item) for item in row]
            writer.writerow(escaped_row)
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


class BasePlatformSettingsAdmin(SingletonAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


def log_action(obj, user, change_message='Changed', action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=change_message
    )


@admin.register(TranslationPlatformSettings)
class TranslationPlatformSettingsAdmin(TranslatableAdmin, BasePlatformSettingsAdmin):
    pass
