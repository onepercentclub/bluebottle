# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import models

from bluebottle.payments.models import Payment


class VitepayPayment(Payment):

    # payment[language_code]	Oui	Langue dans laquelle la transaction
    # est effectuée. Par défault: fr (français).
    # Les codes supportés sont: fr, en
    language_code = models.CharField(max_length=10, default='en')

    # payment[currency_code]	Oui	La devise internationale (ISO-4217)
    # de la transaction en cours. Par défault: XOF (Communauté Financière Africaine (BCEAO))
    currency_code = models.CharField(max_length=10, default='XOF')

    # payment[country_code]	Oui	Le code ISO du pays du site marchant.
    # Valeur par défaut: ML (Mali)
    country_code = models.CharField(max_length=10, default='ML')

    # payment[order_id]	Oui	Le numéro de commande sur le site marchand.
    # Les numéros de commande doivent être uniques sur le site marchand
    # car VitePay n'accepte pas les doublons à ce niveau.
    order_id = models.CharField(max_length=10, null=True)

    # payment[description]	Oui	Une description de l'achat effectué
    # par le client (160 caractères au maximum).
    description = models.CharField(max_length=500, null=True)

    # payment[amount_100]	Oui	Le montant total de la transaction (x100).
    # Ex: Si le montant du panier est de 12500 XOF, la valeur
    # transmise à ce niveau doit être payment[amount_100] = 1250000
    amount_100 = models.IntegerField(null=True)

    # payment[buyer_ip_adress]	Non	L'adresse IP du client qui effectue le paiement.
    buyer_ip_adress = models.CharField(max_length=200, null=True)

    # payment[return_url]	Oui	URL de votre site marchand vers laquelle
    # VitePay redirigera le client si le paiement est effectué avec succès.
    return_url = models.CharField(max_length=500, null=True)

    # payment[decline_url]	Oui	URL de votre site marchand vers laquelle
    # VitePay redirigera le client si le paiement est rejeté.
    decline_url = models.CharField(max_length=500, null=True)

    # payment[cancel_url]	Oui	URL de votre site marchand vers laquelle
    # VitePay redirigera le client si ce(tte) dernie(ère) annule le paiement
    cancel_url = models.CharField(max_length=500, null=True)

    # payment[callback_url]	Oui	Cette URL sera utilisé à l'étape 5 pour
    # confirmer la transaction.
    callback_url = models.CharField(max_length=500, null=True)

    # payment[email]	Non	Email du client qui effectue la transaction.
    email = models.CharField(max_length=500, null=True)

    # payment[p_type] Oui Vous devez obligatoirement transmettre la
    # valeur fixe: 'orange_money' pour spécifier qu'il s'agit bien d'une
    # transaction de paiement avec Orange Money.
    p_type = models.CharField(max_length=500, default='orange_money')

    payment_url = models.CharField(max_length=500, null=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Interswitch Payment"
        verbose_name_plural = "Interswitch Payments"

    def get_method_name(self):
        """ Return the payment method name."""
        return 'vitepay'

    def get_fee(self):
        """
        a fee of 1.5% of the value of the transaction subject to a cap
        of N2,000 is charged. (i.e. for transactions below N133,333, a
        fee of 1.5% applies), and N2,000 flat fee (for transactions above N133,333).
        """
        fee = round(self.order_payment.amount * Decimal(0.015), 2)
        if fee > 2000:
            return 2000
        return fee
