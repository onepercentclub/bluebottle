from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Funding
from bluebottle.funding_lipisha.models import LipishaBankAccount


class MigrateToLipishaEffect(Effect):
    conditions = []
    title = _('Migrate to Lipisha account')
    template = 'admin/migrate_to_lipisha_effect.html'

    def post_save(self, **kwargs):
        account = self.instance
        lipisha = LipishaBankAccount.objects.create(
            connect_account=account.connect_account,
            account_number=account.account_number,
            account_name=account.account_holder_name,
            bank_name=account.bank_name,
            bank_code='',
            branch_name='',
            branch_code='',
            address='',
            swift=''
        )
        Funding.objects.filter(bank_account=account).update(bank_account=lipisha)

    def __str__(self):
        return _('Create a new Lipisha account based on this bank account.')
