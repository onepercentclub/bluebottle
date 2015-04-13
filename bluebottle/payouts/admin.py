import logging
import re

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.admin.sites import NotRegistered

from bluebottle.bb_payouts.admin import BaseProjectPayoutAdmin, BaseOrganizationPayoutAdmin
from bluebottle.utils.model_dispatcher import get_project_payout_model, get_organization_payout_model
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.clients import properties
from bluebottle.payouts.models import ProjectPayout

logger = logging.getLogger(__name__)


PROJECT_PAYOUT_MODEL = get_project_payout_model()
ORGANIZATION_PAYOUT_MODEL = get_organization_payout_model()


class PayoutListFilter(admin.SimpleListFilter):
    title = _('Payout rule')
    parameter_name = 'payout_rule'

    def lookups(self, request, model_admin):
        rules = getattr(properties, 'PROJECT_PAYOUT_FEES', {})
        rule_choices = ProjectPayout.PayoutRules.choices

        return tuple(sorted(((k, "{0}% ({1})".format(int(v*100), k)) for k, v in rules.iteritems()), key=lambda x: int(re.search(r'\d+', x[1]).group(0))))

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            return queryset.filter(payout_rule=self.value())


class LegacyPayoutListFilter(admin.SimpleListFilter):
    title = _('Legacy payout rule')
    parameter_name = 'legacy_payout_rule'

    def lookups(self, request, model_admin):
        return (
            ('old', _('Old')),
            ('zero', _('0%')),
            ('five', _('5%')),
            ('seven', _('7%')),
            ('twelve', _('12%')),
            ('hundred', _('100%')),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            return queryset.filter(payout_rule=self.value())


class OrganizationPayoutAdmin(BaseOrganizationPayoutAdmin):

    actions = ('export_sepa', )

    def export_sepa(self, request, queryset):
        """
        Dowload a sepa file with selected ProjectPayments
        """
        objs = queryset.all()
        if not request.user.is_staff:
            raise PermissionDenied
        response = HttpResponse(mimetype='text/xml')
        date = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')
        response['Content-Disposition'] = 'attachment; filename=payments_sepa%s.xml' % date
        response.write(ORGANIZATION_PAYOUT_MODEL.create_sepa_xml(objs))
        return response

    export_sepa.short_description = "Export SEPA file."

try:
    admin.site.unregister(ORGANIZATION_PAYOUT_MODEL)
except NotRegistered:
    pass
admin.site.register(ORGANIZATION_PAYOUT_MODEL, OrganizationPayoutAdmin)


class ProjectPayoutAdmin(BaseProjectPayoutAdmin):
    
    export_fields = ['project', 'status', 'payout_rule', 'amount_raised', 'organization_fee', 'amount_payable',
                     'created', 'submitted']

    actions = ('change_status_to_new', 'change_status_to_progress', 'change_status_to_settled',
               'export_sepa', 'recalculate_amounts', export_as_csv_action(fields=export_fields))

    def get_list_filter(self, request):
        # If site has a legacy payout rule then display the legacy filter
        if PROJECT_PAYOUT_MODEL.objects.filter(payout_rule__in=['old','five','seven','twelve','hundred']).count():
            return ['status', PayoutListFilter, LegacyPayoutListFilter, 'project__partner_organization']
        else:
            return ['status', PayoutListFilter, 'project__partner_organization']

    def export_sepa(self, request, queryset):
        """
        Dowload a sepa file with selected ProjectPayments
        """
        objs = queryset.all()
        if not request.user.is_staff:
            raise PermissionDenied
        response = HttpResponse(mimetype='text/xml')
        date = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')
        response['Content-Disposition'] = 'attachment; filename=payments_sepa%s.xml' % date
        response.write(PROJECT_PAYOUT_MODEL.create_sepa_xml(objs))
        return response

    export_sepa.short_description = "Export SEPA file."

try:
    admin.site.unregister(PROJECT_PAYOUT_MODEL)
except NotRegistered:
    pass
admin.site.register(PROJECT_PAYOUT_MODEL, ProjectPayoutAdmin)
