from __future__ import unicode_literals

from django.db import migrations, connection, models
from django.contrib.gis.geos import Point

from bluebottle.clients import properties


def map_status(status):
    mapping = {
        'plan-new': 'draft',
        'plan-submitted': 'submitted',
        'plan-needs-work': 'needs_work',
        'voting': 'approved',
        'voting-done': 'approved',
        'campaign': 'approved',
        'to-be-continued': 'approved',
        'done-complete': 'approved',
        'done-incomplete': 'approved',
        'closed': 'closed',
        'refunded': 'approved',
    }
    return mapping[status.slug]


def map_funding_status(status):
    mapping = {
        'plan-new': 'in_review',
        'plan-submitted': 'in_review',
        'plan-needs-work': 'in_review',
        'voting': 'open',
        'voting-done': 'open',
        'campaign': 'open',
        'to-be-continued': 'open',
        'done-complete': 'succeeded',
        'done-incomplete': 'succeeded',
        'closed': 'closed',
        'refunded': 'refunded',
    }
    return mapping[status.slug]


def map_funding_review_status(status):
    mapping = {
        'plan-new': 'draft',
        'plan-submitted': 'submitted',
        'plan-needs-work': 'needs_work',
        'voting': 'approved',
        'voting-done': 'approved',
        'campaign': 'approved',
        'to-be-continued': 'approved',
        'done-complete': 'approved',
        'done-incomplete': 'approved',
        'closed': 'approved',
        'refunded': 'approved',
    }
    return mapping[status.slug]


def truncate(number, limit):
    return int(number * pow(10, limit)) / 10 ^ pow(10, limit)


def set_currencies(apps, provider, name):
    PaymentCurrency = apps.get_model('funding', 'PaymentCurrency')
    defaults = properties.DONATION_AMOUNTS
    for method in properties.PAYMENT_METHODS:
        if method['provider'] == name:
            for cur in method['currencies']:
                val = method['currencies'][cur]
                PaymentCurrency.objects.get_or_create(
                    provider=provider,
                    code=cur,
                    defaults={
                        'min_amount': getattr(val, 'min_amount', 5.0),
                        'default1': defaults[cur][0],
                        'default2': defaults[cur][1],
                        'default3': defaults[cur][2],
                        'default4': defaults[cur][3],
                    }
                )


def migrate_payment_providers(apps):

    PledgePaymentProvider = apps.get_model('funding_pledge', 'PledgePaymentProvider')
    StripePaymentProvider = apps.get_model('funding_stripe', 'StripePaymentProvider')
    FlutterwavePaymentProvider = apps.get_model('funding_flutterwave', 'FlutterwavePaymentProvider')
    VitepayPaymentProvider = apps.get_model('funding_vitepay', 'VitepayPaymentProvider')
    LipishaPaymentProvider = apps.get_model('funding_lipisha', 'LipishaPaymentProvider')

    Client = apps.get_model('clients', 'Client')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    properties.set_tenant(tenant)

    for provider in properties.MERCHANT_ACCOUNTS:
        pp = None
        if provider['merchant'] == 'stripe':
            content_type = ContentType.objects.get_for_model(StripePaymentProvider)
            pp = StripePaymentProvider.objects.create(
                polymorphic_ctype=content_type,
            )
            for payment_methods in properties.PAYMENT_METHODS:
                if payment_methods['id'] == 'stripe-creditcard':
                    pp.credit_card = True
                elif payment_methods['id'] == 'stripe-ideal':
                    pp.ideal = True
                elif payment_methods['id'] == 'stripe-directdebit':
                    pp.direct_debit = True
                elif payment_methods['id'] == 'stripe-bancontact':
                    pp.bancontact = True
            pp.save()
            set_currencies(apps, pp, 'stripe')

        elif provider['merchant'] == 'vitepay':
            content_type = ContentType.objects.get_for_model(VitepayPaymentProvider)
            pp = VitepayPaymentProvider.objects.create(
                polymorphic_ctype=content_type,
                api_secret=provider['api_secret'],
                api_key=provider['api_key'],
                api_url=provider['api_url'],
                prefix='new'
            )
            set_currencies(apps, pp, 'vitepay')
        elif provider['merchant'] == 'lipisha':
            content_type = ContentType.objects.get_for_model(LipishaPaymentProvider)
            pp = LipishaPaymentProvider.objects.create(
                polymorphic_ctype=content_type,
                api_key=provider['api_key'],
                api_signature=provider['api_signature'],
                paybill=provider['business_number'],
                prefix='new'
            )
            set_currencies(apps, pp, 'lipisha')
        elif provider['merchant'] == 'flutterwave':
            content_type = ContentType.objects.get_for_model(FlutterwavePaymentProvider)
            pp = FlutterwavePaymentProvider.objects.create(
                polymorphic_ctype=content_type,
                pub_key=provider['pub_key'],
                sec_key=provider['sec_key'],
                prefix='new'
            )
            set_currencies(apps, pp, 'flutterwave')
        elif provider['merchant'] == 'pledge':
            content_type = ContentType.objects.get_for_model(PledgePaymentProvider)
            pp = PledgePaymentProvider.objects.create(
                polymorphic_ctype=content_type,
            )
            set_currencies(apps, pp, 'pledge')


def migrate_projects(apps, schema_editor):
    migrate_payment_providers(apps)

    Project = apps.get_model('projects', 'Project')
    Initiative = apps.get_model('initiatives', 'Initiative')
    Funding = apps.get_model('funding', 'Funding')
    Geolocation = apps.get_model('geo', 'Geolocation')
    Country = apps.get_model('geo', 'Country')
    Image = apps.get_model('files', 'Image')
    Client = apps.get_model('clients', 'Client')
    OrganizationContact = apps.get_model('organizations', 'OrganizationContact')
    StripePayoutAccount = apps.get_model('funding_stripe', 'StripePayoutAccount')
    ExternalAccount = apps.get_model('funding_stripe', 'ExternalAccount')
    PlainPayoutAccount = apps.get_model('funding', 'PlainPayoutAccount')
    PayoutAccount = apps.get_model('funding', 'PayoutAccount')
    BudgetLine = apps.get_model('funding', 'BudgetLine')
    Reward = apps.get_model('funding', 'Reward')
    Fundraiser = apps.get_model('funding', 'Fundraiser')
    OldPayoutAccount = apps.get_model('payouts', 'PayoutAccount')
    FlutterwaveBankAccount = apps.get_model('funding_flutterwave', 'FlutterwaveBankAccount')
    VitepayBankAccount = apps.get_model('funding_vitepay', 'VitepayBankAccount')
    LipishaBankAccount = apps.get_model('funding_lipisha', 'LipishaBankAccount')
    PledgeBankAccount = apps.get_model('funding_pledge', 'PledgeBankAccount')

    Wallpost = apps.get_model('wallposts', 'Wallpost')

    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Clean-up previous migrations of projects to initiatives
    Initiative.objects.all().delete()

    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    properties.set_tenant(tenant)

    stripe_bank_ct = ContentType.objects.get_for_model(ExternalAccount)
    stripe_account_ct = ContentType.objects.get_for_model(StripePayoutAccount)
    plain_account_ct = ContentType.objects.get_for_model(PlainPayoutAccount)
    flutterwave_ct = ContentType.objects.get_for_model(FlutterwaveBankAccount)
    lipisha_ct = ContentType.objects.get_for_model(LipishaBankAccount)
    vitepay_ct = ContentType.objects.get_for_model(VitepayBankAccount)
    pledge_ct = ContentType.objects.get_for_model(PledgeBankAccount)
    funding_ct = ContentType.objects.get_for_model(Funding)
    project_ct = ContentType.objects.get_for_model(Project)
    initiative_ct = ContentType.objects.get_for_model(Initiative)

    for project in Project.objects.select_related('payout_account', 'projectlocation').iterator():
        if hasattr(project, 'projectlocation') and project.projectlocation.country:
            if project.projectlocation.latitude and project.projectlocation.longitude:
                point = Point(
                    float(project.projectlocation.longitude),
                    float(project.projectlocation.latitude)
                )
            else:
                point = Point(0, 0)

            country = project.country

            if not country and project.projectlocation.country and Country.objects.filter(
                    translations__name=project.projectlocation.country
                ).count():
                country = Country.objects.filter(
                    translations__name__contains=project.projectlocation.country
                ).first()

            if not country:
                country = Country.objects.filter(alpha2_code=properties.DEFAULT_COUNTRY_CODE).first()

            if country:
                place = Geolocation.objects.create(
                    street=project.projectlocation.street,
                    postal_code=project.projectlocation.postal_code,
                    country=country,
                    locality=project.projectlocation.city,
                    position=point
                )
            else:
                place = None
        else:
            if project.country:
                place = Geolocation.objects.create(
                    country=project.country,
                    position=Point(0, 0)
                )
            else:
                place = None

        initiative = Initiative.objects.create(
            title=project.title,
            slug=project.slug,
            pitch=project.pitch or '',
            story=project.story or '',
            theme_id=project.theme_id,
            video_url=project.video_url,
            place=place,
            location_id=project.location_id,
            owner_id=project.owner_id,
            reviewer_id=project.reviewer_id,
            activity_manager_id=project.task_manager_id,
            promoter_id=project.promoter_id,
            status=map_status(project.status)

        )
        if project.image:
            try:
                image = Image.objects.create(owner=project.owner)
                image.file.save(project.image.name, project.image.file, save=True)
                initiative.image = image
            except IOError:
                pass

        if project.organization:
            initiative.organization = project.organization

        contact = OrganizationContact.objects.filter(organization=project.organization).first()
        if contact:
            initiative.organization_contact = contact

        initiative.created = project.created
        initiative.categories = project.categories.all()
        initiative.save()

        # Create Funding event if there are donations
        if project.project_type in ['both', 'funding'] \
                or project.donation_set.count() \
                or project.amount_asked.amount:
            account = None
            if project.payout_account:
                try:
                    stripe_account = project.payout_account.stripepayoutaccount
                    if stripe_account.account_id:
                        payout_account = StripePayoutAccount.objects.create(
                            polymorphic_ctype=stripe_account_ct,
                            account_id=stripe_account.account_id,
                            owner=stripe_account.user,
                            # country=stripe_account.country.alpha2_code
                        )
                        account = ExternalAccount.objects.create(
                            polymorphic_ctype=stripe_bank_ct,
                            connect_account=payout_account,
                            # account_id=stripe_account.bank_details.account
                        )
                except OldPayoutAccount.DoesNotExist:
                    plain_account = project.payout_account.plainpayoutaccount
                    payout_account = PlainPayoutAccount.objects.create(
                        polymorphic_ctype=plain_account_ct,
                        owner=plain_account.user,
                        reviewed=plain_account.reviewed
                    )

                    if str(project.amount_asked.currency) == 'NGN':
                        country = None
                        if plain_account.account_bank_country:
                            country = plain_account.account_bank_country.alpha2_code
                        account = FlutterwaveBankAccount.objects.create(
                            polymorphic_ctype=flutterwave_ct,
                            connect_account=payout_account,
                            account_holder_name=plain_account.account_holder_name,
                            bank_country_code=country,
                            account_number=plain_account.account_number
                        )
                    elif str(project.amount_asked.currency) == 'KES':
                        account = LipishaBankAccount.objects.create(
                            polymorphic_ctype=lipisha_ct,
                            connect_account=payout_account,
                            account_number=plain_account.account_number,
                            account_name=plain_account.account_holder_name,
                            address=plain_account.account_holder_address
                        )
                    elif str(project.amount_asked.currency) == 'XOF':
                        account = VitepayBankAccount.objects.create(
                            polymorphic_ctype=vitepay_ct,
                            connect_account=payout_account,
                            account_name=plain_account.account_holder_name,
                        )
                    else:
                        account = PledgeBankAccount.objects.create(
                            polymorphic_ctype=pledge_ct,
                            connect_account=payout_account,
                            account_holder_name=plain_account.account_holder_name,
                            account_holder_address=plain_account.account_holder_address,
                            account_holder_postal_code=plain_account.account_holder_postal_code,
                            account_holder_city=plain_account.account_holder_city,
                            account_holder_country_id=plain_account.account_holder_country_id,
                            account_number=plain_account.account_number,
                            account_details=plain_account.account_details,
                            account_bank_country_id=plain_account.account_bank_country_id,
                        )

            funding = Funding.objects.create(
                # Common activity fields
                polymorphic_ctype=funding_ct,  # This does not get set automatically in migrations
                initiative=initiative,
                owner_id=project.owner_id,
                highlight=project.is_campaign,
                created=project.created,
                updated=project.updated,
                status=map_funding_status(project.status),
                review_status=map_funding_review_status(project.status),
                title=project.title,
                slug=project.slug,
                description=project.pitch or '',
                transition_date=project.campaign_ended,

                # Funding specific fields
                deadline=project.deadline,
                target=project.amount_asked,
                amount_matching=project.amount_extra,
                country=project.country,
                bank_account=account
            )
            project.funding_id = funding.id
            project.save()

            Wallpost.objects.filter(content_type=project_ct, object_id=project.id).\
                update(content_type=funding_ct, object_id=funding.id)

            for budget_line in project.projectbudgetline_set.all():
                new_budget_line = BudgetLine.objects.create(
                    activity=funding,
                    amount=budget_line.amount,
                    description=budget_line.description,
                    created=budget_line.created,
                    updated=budget_line.updated
                )

            fundraiser_ct = ContentType.objects.get_for_model(Initiative)
            old_fundraiser_ct = ContentType.objects.get_for_model(Project)

            for fundraiser in project.fundraiser_set.all():
                new_fundraiser = Fundraiser.objects.create(
                    owner_id=fundraiser.owner_id,
                    activity=funding,
                    title=fundraiser.title,
                    description=fundraiser.description,
                    amount=fundraiser.amount,
                    deadline=fundraiser.deadline,
                    created=fundraiser.created,
                    updated=fundraiser.updated
                )
                new_fundraiser.save()
                if fundraiser.image:
                    try:
                        image = Image.objects.create(owner=fundraiser.owner)
                        image.file.save(fundraiser.image.name, fundraiser.image.file, save=True)
                        initiative.image = image
                    except IOError:
                        pass
                Wallpost.objects.filter(content_type=old_fundraiser_ct, object_id=fundraiser.id). \
                    update(content_type=fundraiser_ct, object_id=new_fundraiser.id)

            for reward in project.reward_set.all():
                new_reward = Reward.objects.create(
                    activity=funding,
                    amount=reward.amount,
                    description=reward.description,
                    title=reward.title,
                    limit=reward.limit,
                    created=reward.created,
                    updated=reward.updated
                )
                reward.new_reward_id = new_reward.id
                reward.save()
        else:
            Wallpost.objects.filter(content_type=project_ct, object_id=project.id).\
                update(content_type=initiative_ct, object_id=initiative.id)


def wipe_initiatives(apps, schema_editor):

    Initiative = apps.get_model('initiatives', 'Initiative')
    Funding = apps.get_model('funding', 'Funding')
    PaymentProvider = apps.get_model('funding', 'PaymentProvider')

    PaymentProvider.objects.all().delete()
    Initiative.objects.all().delete()
    Funding.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0090_merge_20190222_1101'),
        ('funding', '0042_auto_20191104_1154'),
        ('funding_lipisha', '0006_auto_20191001_2251'),
        ('funding_vitepay', '0007_auto_20191002_0903'),
        ('funding_flutterwave', '0005_auto_20191002_0903'),
        ('funding_stripe', '0001_initial'),
        ('funding_pledge', '0004_pledgebankaccount'),
        ('rewards', '0009_auto_20191104_1230'),
        ('initiatives', '0017_auto_20191031_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='funding_id',
            field=models.IntegerField(null=True),
        ),
        migrations.RunPython(migrate_projects, wipe_initiatives)
    ]
