import csv

from adminfilters.multiselect import UnionFieldListFilter
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.db.models.fields.files import FieldFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.template.response import TemplateResponse
from django_singleton_admin.admin import SingletonAdmin
from moneyed import Money

from bluebottle.clients import properties
from bluebottle.fsm import TransitionNotAllowed
from bluebottle.members.models import Member, CustomMemberFieldSettings, CustomMemberField
from bluebottle.projects.models import CustomProjectFieldSettings, Project, CustomProjectField
from bluebottle.tasks.models import TaskMember
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.forms import FSMModelForm
from bluebottle.utils.forms import TransitionConfirmationForm
from .models import Language


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


def escape_csv_formulas(item):
    if item and item[0] in ['=', '+', '-', '@']:
        return "'" + item
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
            writer.writerow([escape_csv_formulas(item) for item in row])

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
            writer.writerow([escape_csv_formulas(item) for item in row])
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


class FSMAdmin(admin.ModelAdmin):
    form = FSMModelForm

    readonly_fields = ['status']

    def get_transition(self, instance, name):
        transitions = instance.transitions.all_transitions
        for transition in transitions:
            if transition.name == name:
                return transition

    def transition(self, request, pk, transition_name, send_messages=True):
        link = reverse(
            'admin:{}_{}_change'.format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            args=(pk, )
        )

        if not request.user.has_perm('initiative.change_initiative'):
            messages.error(request, 'Missing permission: initiative.change_initiative')
            return HttpResponseRedirect(link)

        instance = self.model.objects.get(pk=pk)
        form = TransitionConfirmationForm(request.POST)
        transition = self.get_transition(instance, transition_name)

        if not transition:
            messages.error(
                request,
                'Transition not allowed: {}'.format(transition_name)
            )
            return HttpResponseRedirect(link)

        if 'confirm' in request.POST and request.POST['confirm']:
            if form.is_valid():
                send_messages = form.cleaned_data['send_messages']

                try:
                    getattr(instance.transitions, transition.name)(
                        send_messages=send_messages,
                        user=request.user
                    )

                    instance.save()
                    log_action(
                        instance,
                        request.user,
                        'Changed status to {}'.format(transition.name)
                    )

                    return HttpResponseRedirect(link)
                except TransitionNotAllowed:
                    errors = transition.errors(instance)
                    if errors:
                        template = loader.get_template(
                            'admin/transition_errors.html'
                        )
                        error_message = template.render({'errors': errors})
                    else:
                        error_message = 'Transition not allowed: {}'.format(transition.name)

                    messages.error(request, error_message)

                    return HttpResponseRedirect(link)

        transition_messages = []
        for message_list in [message(instance).get_messages() for message in transition.options.get('messages', [])]:
            transition_messages += message_list

        context = dict(
            self.admin_site.each_context(request),
            title=TransitionConfirmationForm.title,
            action=transition.name,
            opts=self.model._meta,
            obj=instance,
            pk=instance.pk,
            form=form,
            source=instance.status,
            notifications=transition_messages,
            target=transition.name,
        )

        return TemplateResponse(
            request, 'admin/transition_confirmation.html', context
        )

    def get_urls(self):
        urls = super(FSMAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/transition/(?P<transition_name>.+)$',
                self.admin_site.admin_view(self.transition),
                name='{}_{}_transition'.format(self.model._meta.app_label, self.model._meta.model_name),
            ),
        ]
        return custom_urls + urls
