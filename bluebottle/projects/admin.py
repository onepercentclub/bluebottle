import csv
import logging
from collections import OrderedDict

import six
from adminfilters.multiselect import UnionFieldListFilter
from adminsortable.admin import SortableTabularInline, NonSortableParentAdmin
from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import connection
from django.db import models
from django.db.models import Count, Sum, F, When, Case
from django.forms.models import ModelFormMetaclass
from django.http.response import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_summernote.admin import SummernoteInlineModelAdmin
from django_summernote.widgets import SummernoteWidget
from moneyed.classes import Money
from parler.admin import TranslatableAdmin
from polymorphic.admin.helpers import PolymorphicInlineSupportMixin
from polymorphic.admin.inlines import StackedPolymorphicInline
from schwifty import IBAN, BIC
from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.geo.admin import LocationFilter, LocationGroupFilter
from bluebottle.geo.models import Location
from bluebottle.payments.adapters import has_payment_prodiver
from bluebottle.payments_lipisha.models import LipishaProject
from bluebottle.payouts_dorado.adapters import (
    DoradoPayoutAdapter, PayoutValidationError, PayoutCreationError
)
from bluebottle.projects.decorators import refund_confirmation_form
from bluebottle.projects.forms import ProjectRefundForm
from bluebottle.projects.models import (
    ProjectPlatformSettings, ProjectSearchFilter, ProjectAddOn, ProjectLocation,
    CustomProjectField, CustomProjectFieldSettings, ProjectCreateTemplate)
from bluebottle.rewards.models import Reward
from bluebottle.tasks.admin import TaskAdminInline
from bluebottle.utils.admin import export_as_csv_action, prep_field, LatLongMapPickerMixin, BasePlatformSettingsAdmin, \
    TranslatedUnionFieldListFilter
from bluebottle.utils.widgets import CheckboxSelectMultipleWidget, SecureAdminURLFieldWidget
from bluebottle.votes.models import Vote
from .forms import ProjectDocumentForm
from .models import (ProjectBudgetLine, Project,
                     ProjectDocument, ProjectPhaseLog)
from .tasks import refund_project

logger = logging.getLogger(__name__)


def mark_as(model_admin, request, queryset):
    slug = request.POST['action'].replace('mark_', '')
    try:
        status = ProjectPhase.objects.get(slug=slug)
    except ProjectPhase.DoesNotExist:
        return

    # NOTE: To trigger the post save signals, resist using bulk updates
    # REF: https://docs.djangoproject.com/en/1.10/ref/models/querysets/#update
    projects = Project.objects.filter(pk__in=queryset.values_list('pk', flat=True))
    for project in projects:
        project.status = status
        project.save()


class ProjectThemeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('slug', 'disabled', 'project_link')
    readonly_fields = ('project_link', )
    fields = ('name', 'slug', 'description', 'disabled') + readonly_fields

    def project_link(self, obj):
        url = "{}?theme_filter={}".format(reverse('admin:projects_project_changelist'), obj.id)
        return format_html("<a href='{}'>{} projects</a>".format(url, obj.project_set.count()))
    project_link.short_description = _('Project link')


admin.site.register(ProjectTheme, ProjectThemeAdmin)


class ProjectReviewerFilter(admin.SimpleListFilter):
    title = _('Reviewer')
    parameter_name = 'reviewer'

    def lookups(self, request, model_admin):
        return ((True, _('My projects')), )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                reviewer=request.user
            )
        else:
            return queryset


class ProjectDocumentInline(admin.StackedInline):
    model = ProjectDocument
    form = ProjectDocumentForm
    extra = 0
    raw_id_fields = ('author',)
    readonly_fields = ('download_url',)
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        url = obj.document_url

        if url is not None:
            return format_html(
                u"<a href='{}'>{}</a>",
                str(url), 'Download'
            )
        return '(None)'


class RewardInlineFormset(forms.models.BaseInlineFormSet):

    def clean(self):
        delete_checked = False

        for form in self.forms:
            try:
                if form.cleaned_data:
                    if form.cleaned_data['DELETE'] and form.cleaned_data['id'].count:
                        delete_checked = True
            except ValueError:
                pass

        if delete_checked:
            raise forms.ValidationError(_('You cannot delete a reward that has successful donations.'))


class RewardInlineAdmin(admin.TabularInline):
    model = Reward
    formset = RewardInlineFormset
    readonly_fields = ('count',)
    extra = 0

    def count(self, obj):
        url = reverse('admin:donations_donation_changelist')
        return format_html('<a href={}?reward={}>{}</a>'.format(url, obj.id, obj.count))


class ProjectPhaseLogInline(admin.TabularInline):
    model = ProjectPhaseLog
    can_delete = False
    ordering = ('-start',)
    extra = 0

    def has_add_permission(self, request):
        return False

    readonly_fields = ('status', 'start')
    fields = readonly_fields


class FundingFilter(admin.SimpleListFilter):
    title = _('Funding')
    parameter_name = 'funding'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Crowdfunding')),
            ('no', _('Crowdsourcing')),
            ('both', _('Crowdfunding & crowdsourcing')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(amount_asked__gt=0)
        elif self.value() == 'no':
            from django.db.models import Q
            return queryset.filter(Q(amount_asked=None) | Q(amount_asked=0.00))
        return queryset


class ProjectBudgetLineInline(admin.TabularInline):
    model = ProjectBudgetLine
    extra = 0


class ReviewerWidget(admin.widgets.ForeignKeyRawIdWidget):
    def url_parameters(self):
        parameters = super(ReviewerWidget, self).url_parameters()
        parameters['is_staff'] = True
        return parameters


class CustomAdminFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in CustomProjectFieldSettings.objects.all():
                attrs[field.slug] = forms.CharField(required=False,
                                                    label=field.name,
                                                    help_text=field.description)

        return super(CustomAdminFormMetaClass, cls).__new__(cls, name, bases, attrs)


class ProjectAdminForm(six.with_metaclass(CustomAdminFormMetaClass, forms.ModelForm)):

    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'currencies': CheckboxSelectMultipleWidget,
            'story': SummernoteWidget()
        }

    theme = forms.ModelChoiceField(queryset=ProjectTheme.objects.all().filter(disabled=False))

    def __init__(self, *args, **kwargs):
        super(ProjectAdminForm, self).__init__(*args, **kwargs)
        try:
            self.fields['currencies'].required = False
        except KeyError:
            # Field is not shown
            pass
        self.fields['reviewer'].widget = ReviewerWidget(
            rel=Project._meta.get_field('reviewer').rel,
            admin_site=admin.sites.site
        )
        self.fields['story'].widget.attrs = {'data-project_id': self.instance.pk}

        if connection.tenant.schema_name != 'public':
            for field in CustomProjectFieldSettings.objects.all():
                self.fields[field.slug] = forms.CharField(required=False,
                                                          label=field.name,
                                                          help_text=field.description)

                if CustomProjectField.objects.filter(project=self.instance, field=field).exists():
                    value = CustomProjectField.objects.filter(project=self.instance, field=field).get().value
                    self.initial[field.slug] = value

    def clean(self):
        if (
            'status' in self.cleaned_data and
            self.cleaned_data['status'].slug == 'campaign' and
            'amount_asked' in self.cleaned_data and
            self.cleaned_data['amount_asked'].amount > 0 and
            not self.cleaned_data['bank_details_reviewed']
        ):
            raise forms.ValidationError(
                _('The bank details need to be reviewed before approving a project')
            )
        super(ProjectAdminForm, self).clean()

    def save(self, commit=True):
        project = super(ProjectAdminForm, self).save(commit=commit)
        for field in CustomProjectFieldSettings.objects.all():
            extra, created = CustomProjectField.objects.get_or_create(
                project=project,
                field=field
            )
            extra.value = self.cleaned_data.get(field.slug, None)
            extra.save()
        return project


class ProjectAddOnInline(StackedPolymorphicInline):

    model = ProjectAddOn

    class LipishaProjectInline(StackedPolymorphicInline.Child):
        model = LipishaProject
        readonly_fields = ['paybill_number']

    def get_child_inline_instances(self):
        instances = []
        if connection.schema_name != 'public' and has_payment_prodiver('lipisha'):
            instances.append(self.LipishaProjectInline(parent_inline=self))
        return instances


class ProjectLocationForm(forms.ModelForm):
    class Meta:
        model = ProjectLocation
        widgets = {
            'latitude': forms.TextInput(attrs={'size': 50, 'id': 'id_latitude'}),
            'longitude': forms.TextInput(attrs={'size': 50, 'id': 'id_longitude'}),

        }
        fields = ('latitude', 'longitude')


class ProjectLocationInline(LatLongMapPickerMixin, admin.StackedInline):
    model = ProjectLocation
    readonly_fields = ('place', 'street', 'neighborhood', 'city', 'postal_code', 'country')

    form = ProjectLocationForm
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput(attrs={'size': 70})},
        models.CharField: {'widget': forms.TextInput(attrs={'size': 70})},
    }

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ProjectAdmin(AdminImageMixin, PolymorphicInlineSupportMixin, ImprovedModelForm):
    form = ProjectAdminForm
    date_hierarchy = 'deadline'
    ordering = ('-created',)

    save_as = True
    search_fields = (
        'title', 'owner__first_name', 'owner__last_name', 'owner__email',
        'organization__name', 'organization__contacts__email'
    )
    raw_id_fields = ('owner', 'reviewer', 'task_manager', 'promoter', 'organization',)
    prepopulated_fields = {'slug': ('title',)}

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    class Media:
        css = {
            'all': ('css/admin/wide-actions.css',)
        }
        js = ('admin/js/inline-task-add.js',)

    def get_inline_instances(self, request, obj=None):
        self.inlines = self.all_inlines
        if obj:
            # We need to reload project, or we get an error when changing project type
            project = Project.objects.get(pk=obj.id)
            if project.project_type == 'sourcing':
                self.inlines = self.sourcing_inlines
        elif request.POST.get('project_type', '') == 'sourcing':
            self.inlines = self.sourcing_inlines

        instances = super(ProjectAdmin, self).get_inline_instances(request, obj)
        add_on_inline = ProjectAddOnInline(self.model, self.admin_site)
        if len(add_on_inline.get_child_inline_instances()):
            instances.append(add_on_inline)
        return instances

    all_inlines = (
        ProjectLocationInline,
        ProjectBudgetLineInline,
        RewardInlineAdmin,
        TaskAdminInline,
        ProjectDocumentInline,
        ProjectPhaseLogInline
    )
    sourcing_inlines = (
        ProjectLocationInline,
        ProjectDocumentInline,
        TaskAdminInline,
        ProjectPhaseLogInline
    )

    list_filter = ('country__subregion__region', )

    export_fields = [
        ('title', 'title'),
        ('owner', 'owner'),
        ('owner__remote_id', 'remote id'),
        ('reviewer', 'reviewer'),
        ('task_manager', 'task_manager'),
        ('promoter', 'promoter'),
        ('created', 'created'),
        ('status', 'status'),
        ('payout_status', 'payout status'),
        ('theme', 'theme'),
        ('location__group', 'region'),
        ('country', 'country'),
        ('location', 'location'),
        ('place', 'place'),
        ('deadline', 'deadline'),
        ('date_submitted', 'date submitted'),
        ('campaign_started', 'campaign started'),
        ('campaign_ended', 'campaign ended'),
        ('campaign_funded', 'campaign funded'),
        ('campaign_paid_out', 'campaign paid out'),
        ('task_count', 'task count'),
        ('supporters', 'supporters'),
        ('time_spent', 'time spent'),
        ('amount_asked', 'amount asked'),
        ('amount_donated', 'amount donated'),
        ('organization__name', 'organization'),
        ('amount_extra', 'amount matched'),
        ('expertise_based', 'expertise based'),
    ]

    actions = [export_as_csv_action(fields=export_fields), ]

    def get_actions(self, request):
        actions = super(ProjectAdmin, self).get_actions(request)
        for phase in ProjectPhase.objects.order_by('-sequence').all():
            action_name = 'mark_{}'.format(phase.slug)
            actions[action_name] = (
                mark_as, action_name, _('Mark selected as "{}"'.format(_(phase.name)))
            )
        return OrderedDict(reversed(actions.items()))

    # Fields
    def num_votes(self, obj):
        self.queryset(None)
        return obj.admin_vote_count

    num_votes.short_description = _('Vote Count')
    num_votes.admin_order_field = 'admin_vote_count'

    def get_title_display(self, obj):
        if len(obj.title) > 35:
            return format_html(
                u'<span title="{}" class="project-title">{} &hellip;</span>',
                obj.title, obj.title[:45]
            )
        return obj.title
    get_title_display.admin_order_field = 'title'
    get_title_display.short_description = _('title')

    def get_owner_display(self, obj):
        owner = obj.owner
        url = reverse('admin:members_member_change', args=[owner.id])
        return format_html(
            u"<a href='{}'>{}</a>",
            url,
            owner.get_full_name()
        )

    get_owner_display.admin_order_field = 'owner__last_name'
    get_owner_display.short_description = _('owner')

    def vote_count(self, obj):
        return obj.vote_set.count()

    def donated_percentage(self, obj):
        if obj.amount_donated.amount:
            percentage = 100 * obj.admin_donated_percentage
        else:
            percentage = 0
        return "{0:.2f} %".format(percentage)
    donated_percentage.short_description = _('Donated')
    donated_percentage.admin_order_field = 'admin_donated_percentage'

    def expertise_based(self, obj):
        return obj.expertise_based

    expertise_based.boolean = True

    def approve_payout(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        project_url = reverse('admin:projects_project_change', args=(project.id,))

        # Check IBAN & BIC
        account = project.account_number
        if len(account) < 3:
            self.message_user(request, 'Invalid Bank Account: {}'.format(account), level='ERROR')
            return HttpResponseRedirect(project_url)

        if len(account) and account[0].isalpha():
            # Looks like an IBAN (starts with letter), let's check
            try:
                iban = IBAN(account)
            except ValueError as e:
                self.message_user(request, 'Invalid IBAN: {}'.format(e), level='ERROR')
                return HttpResponseRedirect(project_url)
            project.account_number = iban.compact
            try:
                bic = BIC(project.account_details)
            except ValueError as e:
                self.message_user(request, 'Invalid BIC: {}'.format(e), level='ERROR')
                return HttpResponseRedirect(project_url)
            project.account_details = bic.compact
            project.save()

        if not request.user.has_perm('projects.approve_payout'):
            self.message_user(request, 'Missing permission: projects.approve_payout', level='ERROR')
        elif project.payout_status != 'needs_approval':
            self.message_user(request, 'The payout does not have the status "needs approval"', level='ERROR')
        else:
            adapter = DoradoPayoutAdapter(project)
            try:
                adapter.trigger_payout()
            except PayoutValidationError as e:
                errors = e.message['errors']
                if type(errors) == unicode:
                    self.message_user(
                        request,
                        'Account details: {}.'.format(errors),
                        level=messages.ERROR
                    )
                else:
                    for field, errors in errors.items():
                        for error in errors:
                            self.message_user(
                                request,
                                'Account details: {}, {}.'.format(field, error.lower()),
                                level=messages.ERROR
                            )
            except (PayoutCreationError, ImproperlyConfigured) as e:
                logger.warning(
                    'Error approving payout: {}'.format(e),
                    exc_info=1
                )

                self.message_user(
                    request,
                    'Failed to approve payout: {}'.format(e),
                    level=messages.ERROR
                )

        return HttpResponseRedirect(project_url)

    @refund_confirmation_form(ProjectRefundForm)
    def refund(self, request, pk=None, form=None):
        project = Project.objects.get(pk=pk)

        if not request.user.has_perm('payments.refund_orderpayment') or not project.can_refund:
            return HttpResponseForbidden('Missing permission: payments.refund_orderpayment')

        project.status = ProjectPhase.objects.get(slug='refunded')
        project.save()

        refund_project.delay(connection.tenant, project)

        project_url = reverse('admin:projects_project_change', args=(project.id,))
        return HttpResponseRedirect(project_url)

    reward_export_fields = (
        ('reward__title', 'Reward'),
        ('reward__description', 'Description'),
        ('order__id', 'Order id'),
        ('created', 'Donation Date'),
        ('reward__amount', 'Amount'),
        ('amount', 'Actual Amount'),
        ('order__user__email', 'Email'),
        ('order__user__full_name', 'Name'),
        ('name', 'Name on Donation')
    )

    def export_rewards(self, request, pk=None):
        """ Export all donations that include a reward.

        This allows the project initiator to contact all recipients.
        """
        project = Project.objects.get(pk=pk)
        if not request.user.is_staff:
            return HttpResponseForbidden('Missing permission: rewards.read_reward')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            unicode(slugify(project.title))
        )

        writer = csv.writer(response)

        writer.writerow([field[1] for field in self.reward_export_fields])

        for reward in project.donations.filter(reward__isnull=False):
            writer.writerow([
                prep_field(request, reward, field[0]) for field in self.reward_export_fields
            ])

        return response

    def amount_donated_i18n(self, obj):
        return obj.amount_donated

    amount_donated_i18n.short_description = _('Amount Donated')

    def amount_needed_i18n(self, obj):
        amount_needed = obj.amount_needed - obj.amount_extra
        if amount_needed.amount > 0:
            return amount_needed
        else:
            return Money(0, obj.amount_asked.currency)

    amount_needed_i18n.short_description = _('Amount Needed')

    # Setup
    def get_readonly_fields(self, request, obj=None):
        fields = [
            'created', 'updated',
            'vote_count', 'amount_donated_i18n', 'amount_needed_i18n',
            'popularity', 'payout_status',
            'geocoding'
        ]
        if obj and obj.payout_status and obj.payout_status != 'needs_approval':
            fields += ('status', )
        return fields

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        process_urls = [
            url(r'^approve_payout/(?P<pk>\d+)/$',
                self.approve_payout,
                name="projects_project_approve_payout"),
            url(r'^refund/(?P<pk>\d+)/$',
                self.refund,
                name="projects_project_refund"),
            url(r'^export_rewards/(?P<pk>\d+)/$',
                self.export_rewards,
                name="projects_project_export_rewards"),
        ]
        return process_urls + urls

    def get_list_filter(self, request):
        filters = [
            ('status', UnionFieldListFilter),
            ('theme', TranslatedUnionFieldListFilter),
            ('task__skill', TranslatedUnionFieldListFilter),
            ProjectReviewerFilter,
            'categories',
            'project_type',
        ]

        if request.user.has_perm('projects.approve_payout'):
            filters.insert(1, 'payout_status')

        # Only show Location column if there are any
        if Location.objects.count():
            filters += [LocationGroupFilter, LocationFilter]
        else:
            filters += [('country', admin.RelatedOnlyFieldListFilter), ]
        return filters

    def get_list_display(self, request):
        fields = [
            'get_title_display', 'get_owner_display', 'created_date',
            'status', 'deadline_date', 'donated_percentage',
            'expertise_based'
        ]

        if request.user.has_perm('projects.approve_payout'):
            fields.insert(4, 'payout_status')

        # Only show Location column if there are any
        if Location.objects.count():
            fields += ('location',)
        # Only show Vote_count column if there are any votes
        if Vote.objects.count():
            fields += ('vote_count',)
        return fields

    def lookup_allowed(self, key, value):
        if key == 'task__skill__expertise__exact':
            return True
        else:
            return super(ProjectAdmin, self).lookup_allowed(key, value)

    def created_date(self, obj):
        return obj.created.date()
    created_date.admin_order_field = 'created'
    created_date.short_description = _('Created')

    def deadline_date(self, obj):
        if obj.deadline:
            return obj.deadline.date()
        return None
    deadline_date.admin_order_field = 'deadline'
    deadline_date.short_description = _('Deadline')

    def get_fieldsets(self, request, obj=None):
        main = (_('Main'), {'fields': [
            'reviewer', 'title', 'slug', 'project_type',
            'status', 'owner', 'task_manager', 'promoter',
            'organization', 'is_campaign', 'celebrate_results'
        ]})

        story = (_('Story'), {'fields': [
            'pitch', 'story',
            'image', 'video_url',
            'theme', 'categories', 'language',
            'country', 'place',
        ]})

        if Location.objects.count():
            story[1]['fields'].append('location')

        amount = (_('Amount'), {'fields': [
            'amount_asked', 'amount_extra', 'amount_donated_i18n', 'amount_needed_i18n',
            'currencies', 'popularity', 'vote_count'
        ]})

        if request.user.has_perm('projects.approve_payout'):
            amount[1]['fields'].insert(0, 'payout_status')

        dates = (_('Dates'), {'fields': [
            'created', 'updated',
            'deadline', 'date_submitted', 'campaign_started',
            'campaign_ended', 'campaign_funded',
            'campaign_paid_out', 'voting_deadline'
        ]})

        bank = (_('Bank details'), {'fields': [
            'account_holder_name',
            'account_holder_address',
            'account_holder_postal_code',
            'account_holder_city',
            'account_holder_country',
            'account_number',
            'account_details',
            'account_bank_country',
            'bank_details_reviewed'
        ]})

        extra = (_('Extra fields'), {
            'fields': [field.slug for field in CustomProjectFieldSettings.objects.all()]
        })

        fieldsets = (main, story, dates)

        if obj:
            project = Project.objects.get(pk=obj.id)
            if project.project_type != 'sourcing':
                fieldsets += (amount, bank)

        if CustomProjectFieldSettings.objects.count():
            fieldsets += (extra, )

        return fieldsets

    def get_queryset(self, request):
        # Optimization: Select related fields that are used in admin specific
        # display fields.
        queryset = super(ProjectAdmin, self).get_queryset(request)
        queryset = queryset.select_related(
            'owner', 'organization'
        ).annotate(
            admin_vote_count=Count('vote', distinct=True),
            admin_donated_percentage=Case(
                When(amount_asked__gt=0, then=F('amount_donated') / F('amount_asked')),
                default=0
            ),
            time_spent=Sum('task__members__time_spent')
        )

        return queryset


admin.site.register(Project, ProjectAdmin)


class ProjectPhaseAdmin(TranslatableAdmin):
    list_display = ['__unicode__', 'name', 'slug', 'project_link']
    readonly_fields = ('slug', )

    def project_link(self, obj):
        url = "{}?status_filter={}".format(reverse('admin:projects_project_changelist'), obj.id)
        return format_html("<a href='{}'>{} projects</a>".format(url, obj.project_set.count()))

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(ProjectPhase, ProjectPhaseAdmin)


class ProjectSearchFilterInline(SortableTabularInline):
    model = ProjectSearchFilter
    extra = 0


class ProjectCreateTemplateForm(forms.ModelForm):
    class Meta:
        model = ProjectCreateTemplate
        exclude = []
        widgets = {
            'description': SummernoteWidget(attrs={'height': '200px'}),
            'default_description': SummernoteWidget(attrs={'height': '200px'}),
            'default_pitch': AdminTextareaWidget(attrs={'cols': '40', 'rows': '5'})
        }


class ProjectCreateTemplateInline(admin.StackedInline, SummernoteInlineModelAdmin):
    form = ProjectCreateTemplateForm
    model = ProjectCreateTemplate
    extra = 0


class ProjectPlatformSettingsAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'create_types': CheckboxSelectMultipleWidget,
            'contact_types': CheckboxSelectMultipleWidget,
            'share_options': CheckboxSelectMultipleWidget,
        }
    extra = 0


class CustomProjectFieldSettingsInline(SortableTabularInline):
    model = CustomProjectFieldSettings
    readonly_fields = ('slug',)
    extra = 0


class ProjectPlatformSettingsAdmin(BasePlatformSettingsAdmin, NonSortableParentAdmin):

    form = ProjectPlatformSettingsAdminForm
    inlines = [
        ProjectSearchFilterInline,
        CustomProjectFieldSettingsInline,
        ProjectCreateTemplateInline
    ]


admin.site.register(ProjectPlatformSettings, ProjectPlatformSettingsAdmin)
