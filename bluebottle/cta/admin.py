from django.contrib import admin, messages
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import bluebottle.cta.types  # noqa: F401
from bluebottle.cta.framework import get_actions, registry
from bluebottle.cta.models import ActionDismissal
from bluebottle.members.models import Member


class StatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('ignored', _('Ignored')),
            ('snoozed', _('Snoozed')),
            ('expired', _('Snooze expired')),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'ignored':
            return queryset.filter(snoozed_until__isnull=True)
        if self.value() == 'snoozed':
            return queryset.filter(snoozed_until__gt=now)
        if self.value() == 'expired':
            return queryset.filter(snoozed_until__lte=now)
        return queryset


class ActionTypeFilter(admin.SimpleListFilter):
    title = _('action type')
    parameter_name = 'action_type'

    def lookups(self, request, model_admin):
        return [(slug, slug.replace('_', ' ').capitalize()) for slug in registry.types]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(action_type=self.value())
        return queryset


@admin.register(ActionDismissal)
class ActionDismissalAdmin(admin.ModelAdmin):
    change_list_template = 'admin/cta/actiondismissal/change_list.html'

    list_display = ('user', 'action_type', 'object_id', 'status', 'snoozed_until', 'dismissed_at')
    list_filter = (ActionTypeFilter, StatusFilter)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    readonly_fields = ('dismissed_at',)
    date_hierarchy = 'dismissed_at'
    actions = ['restore']

    @admin.display(description=_('status'))
    def status(self, obj):
        if obj.snoozed_until is None:
            return _('Ignored')
        if obj.snoozed_until > timezone.now():
            return _('Snoozed')
        return _('Snooze expired')

    @admin.action(description=_('Restore selected actions to the users\' lists'))
    def restore(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            _('%(count)d actions restored.') % {'count': count},
            messages.SUCCESS,
        )

    def get_urls(self):
        return [
            path(
                'user-actions/',
                self.admin_site.admin_view(self.user_actions),
                name='cta_actiondismissal_user_actions',
            ),
        ] + super().get_urls()

    def user_actions(self, request):
        if not self.has_view_permission(request):
            raise Http404()

        member = None
        items = []
        user_id = request.GET.get('user')
        if user_id and user_id.isdigit():
            member = Member.objects.filter(pk=user_id).first()
            if member:
                items = get_actions(member, include_snoozed=True)

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': _('Current actions for a user'),
            'member': member,
            'user_id': user_id or '',
            'items': items,
            'dismissals_url': reverse('admin:cta_actiondismissal_changelist'),
        }
        return TemplateResponse(request, 'admin/cta/actiondismissal/user_actions.html', context)
