import logging

from bluebottle.bb_payouts.admin import (BaseOrganizationPayoutAdmin,
                                         BaseProjectPayoutAdmin)
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.model_dispatcher import (get_organization_payout_model,
                                               get_project_payout_model)
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


PROJECT_PAYOUT_MODEL = get_project_payout_model()
ORGANIZATION_PAYOUT_MODEL = get_organization_payout_model()


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

    list_filter = ['status', 'payout_rule', 'project__partner_organization']

    export_fields = ['project', 'status', 'payout_rule', 'amount_raised', 'organization_fee', 'amount_payable',
                     'created', 'submitted']

    list_display = ['payout', 'status', 'admin_project', 'amount_payable', 'rule',
                    'admin_has_iban', 'created_date', 'submitted_date', 'completed_date']

    actions = ('change_status_to_new', 'change_status_to_progress', 'change_status_to_settled',
               'export_sepa', 'recalculate_amounts', export_as_csv_action(fields=export_fields))

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
