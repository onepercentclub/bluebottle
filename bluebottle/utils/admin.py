import csv

from adminfilters.multiselect import UnionFieldListFilter
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.db.models.fields.files import FieldFile
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_singleton_admin.admin import SingletonAdmin
from moneyed import Money

from bluebottle.activities.models import Contribution
from bluebottle.clients import properties
from bluebottle.fsm import TransitionNotPossible
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
            if queryset.model is Contribution:
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


class FSMAdminMixin(object):
    form = FSMModelForm

    readonly_fields = ['status']
    transition_selected_confirmation_template = None

    def bulk_transition(self, request, queryset):
        opts = self.model._meta
        app_label = opts.app_label

        if len(set(queryset.values_list('status', flat=True))) > 1:
            self.message_user(
                request,
                'Can only bulk transition {} with the same status.'.format(opts.verbose_name_plural),
                messages.ERROR)
            return None

        if len(queryset) == 1:
            objects_name = force_text(opts.verbose_name)
        else:
            objects_name = force_text(opts.verbose_name_plural)

        # Check that the user has change permission for the actual model
        if not self.has_change_permission(request):
            raise PermissionDenied

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('confirm') and request.POST.get('transition'):
            success = 0
            error = 0
            if queryset.count():
                transition_name = request.POST.get('transition')
                error_list = []
                for obj in queryset.all():
                    transition = self.get_transition(obj, transition_name, 'transitions')
                    try:
                        getattr(obj.transitions, transition_name)()
                        obj.save()
                        success += 1
                        log_action(
                            obj,
                            request.user,
                            'Changed status to {} (Admin bulk)'.format(transition.target)
                        )
                    except TransitionNotPossible:
                        errors = transition.errors(obj.transitions)
                        error_list.append(
                            'Could not transition <i>{}</i> because: <b>{}</b>'.format(obj, ", ".join(errors))
                        )
                        error += 1
                if success:
                    self.message_user(request, _("Successfully transitioned %(count)d %(items)s.") % {
                        "count": success, "items": model_ngettext(opts, success)
                    }, messages.SUCCESS)
                if error:
                    message = format_html("<br>".join(error_list))
                    self.message_user(request, message, messages.ERROR)

            return None

        transitions = queryset[0].transitions.all_transitions
        title = _("Are you sure?")

        context = dict(
            self.admin_site.each_context(request),
            title=title,
            objects_name=objects_name,
            queryset=queryset,
            transitions=transitions,
            opts=opts,
            media=self.media,
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(request, self.transition_selected_confirmation_template or [
            "admin/%s/%s/transition_confirmation.html" % (app_label, opts.model_name),
            "admin/%s/transition_selected_confirmation.html" % app_label,
            "admin/transition_selected_confirmation.html",
            "admin/transition_selected_confirmation.html"
        ], context)

    def get_transition(self, instance, name, field_name):
        transitions = getattr(instance, field_name).all_transitions
        for transition in transitions:
            if transition.name == name:
                return transition

    def transition(self, request, pk, field_name, transition_name, send_messages=True):
        link = reverse(
            'admin:{}_{}_change'.format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            args=(pk, )
        )

        # perform actual check for change permission. using self.model
        permission = '{}.change_{}'.format(
            self.model._meta.app_label, self.model._meta.model_name
        )
        if not request.user.has_perm(permission):
            messages.error(request, 'Missing permission: {}'.format(permission))
            return HttpResponseRedirect(link)

        instance = self.model.objects.get(pk=pk)
        form = TransitionConfirmationForm(request.POST)
        transition = self.get_transition(instance, transition_name, field_name)

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
                    transitions = getattr(instance, field_name)
                    getattr(transitions, transition.name)(
                        send_messages=send_messages
                    )

                    instance.save()
                    log_action(
                        instance,
                        request.user,
                        'Changed status to {}'.format(transition.name)
                    )

                    return HttpResponseRedirect(link)
                except TransitionNotPossible:
                    errors = transition.errors(instance.transitions)
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
        urls = super(FSMAdminMixin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/transition/(?P<field_name>.+)/(?P<transition_name>.+)$',
                self.admin_site.admin_view(self.transition),
                name='{}_{}_transition'.format(self.model._meta.app_label, self.model._meta.model_name),
            ),
        ]
        return custom_urls + urls


class FSMAdmin(FSMAdminMixin, admin.ModelAdmin):

    actions = admin.ModelAdmin.actions + [
        FSMAdminMixin.bulk_transition
    ]
