import csv
import datetime
from builtins import str

import six
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.db.models import ExpressionWrapper, Q, fields
from django.db.models.aggregates import Sum
from django.db.models.fields.files import FieldFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.template import loader
from django.utils.encoding import smart_str
from djmoney.money import Money
from parler.admin import TranslatableAdmin
from solo.admin import SingletonModelAdmin

from bluebottle.activities.models import Contributor
from bluebottle.clients import properties
from bluebottle.members.models import Member
from bluebottle.utils.exchange_rates import convert
from .models import Language, TranslationPlatformSettings
from ..segments.models import SegmentType


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

    if isinstance(attr, Money):
        attr = str(attr)

    if isinstance(attr, datetime.datetime):
        attr = attr.strftime('%d-%m-%y %H:%M')

    if isinstance(attr, datetime.timedelta):
        attr = attr.seconds / (60 * 60)

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

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            str(opts).replace('.', '_')
        )
        writer = csv.writer(response, delimiter=';', dialect='excel')

        if header:
            row = labels if labels else field_names
            if queryset.model is Member or issubclass(queryset.model, Contributor):
                for segment_type in SegmentType.objects.all():
                    labels.append(segment_type.name)
            writer.writerow([escape_csv_formulas(item) for item in row])

        if queryset.model is Member:
            queryset = queryset.prefetch_related('place')
            queryset = queryset.prefetch_related('segments')
            queryset = queryset.prefetch_related('contributor_set')

        for obj in queryset:
            row = [prep_field(request, obj, field, manyToManySep) for field in field_names]

            # Write extra field data
            if queryset.model is Member:
                for segment_type in SegmentType.objects.all():
                    segments = " | ".join(obj.segments.filter(
                        segment_type=segment_type).values_list('name', flat=True))
                    row.append(segments)
            if issubclass(queryset.model, Contributor):
                for segment_type in SegmentType.objects.all():
                    if obj.user:
                        segments = " | ".join(obj.user.segments.filter(
                            segment_type=segment_type).values_list('name', flat=True))
                    else:
                        segments = ''
                    row.append(segments)
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


class BasePlatformSettingsAdmin(SingletonModelAdmin):
    pass


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


class TranslatableAdminOrderingMixin(object):

    translatable_ordering = 'translations__name'

    def get_queryset(self, request):
        language_code = self.get_queryset_language(request)
        queryset = super(TranslatableAdminOrderingMixin, self).get_queryset(request)
        return queryset.filter(
            translations__pk__in=self.model.translations.field.model.objects.annotate(
                is_translated=ExpressionWrapper(
                    Q(language_code=language_code),
                    output_field=fields.BooleanField()
                )
            ).order_by('master_id', '-is_translated').distinct('master_id').values('pk')
        ).order_by(self.translatable_ordering)


def admin_info_box(text):
    template = loader.get_template('admin/info_box.html')
    context = {
        'text': text,
    }
    return template.render(context)
