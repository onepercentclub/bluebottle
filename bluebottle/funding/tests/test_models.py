from moneyed import Money
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, RewardFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingTestCase(BluebottleTestCase):

    def test_absolute_url(self):
        funding = FundingFactory()
        expected = 'http://testserver/en/initiatives/activities/details' \
                   '/funding/{}/{}'.format(funding.id, funding.slug)
        self.assertEqual(funding.get_absolute_url(), expected)

    def test_budget_currency_change(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))

        BudgetLineFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        funding.target = Money(50, 'USD')
        funding.save()

        for line in funding.budget_lines.all():
            self.assertEqual(str(line.amount.currency), 'USD')

    def test_budget_line_required(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))
        errors = list(funding.errors)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[1].message, 'Please specify a budget')

        BudgetLineFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        errors = list(funding.errors)
        self.assertEqual(len(errors), 1)

    def test_reward_currency_change(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))

        RewardFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        funding.target = Money(50, 'USD')
        funding.save()

        for reward in funding.rewards.all():
            self.assertEqual(str(reward.amount.currency), 'USD')
