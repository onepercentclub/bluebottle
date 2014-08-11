if (DEBUG) {
    App.Store.registerAdapter("App.PaymentMethod", App.MockAdapter);
    App.Store.registerAdapter("App.Payment", App.MockAdapter);
    App.Store.registerAdapter("App.MyPayment", App.MockAdapter);
}

App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment-methods',

    provider: DS.attr('string'),
    name: DS.attr('string'),
    profile: DS.attr('string'),

    uniqueId: function () {
        return this.get('provider') + this.get('profile').capitalize();
    }.property('provider', 'profile')
});


App.Payment = DS.Model.extend({
    user: DS.belongsTo('App.UserPreview'),
    order: DS.belongsTo('App.MyOrder'),
    status: DS.attr('string'),
    created: DS.attr('date'),
    updated: DS.attr('date'),
    closed: DS.attr('date'),
    amount: DS.attr('number')
});

App.MyPayment = App.Payment.extend({
    url: 'payments/my',

    payment_method: DS.belongsTo('App.PaymentMethod'),
    // Hosted payment page details
    integrationDetails: DS.attr('object'),
    integrationData: DS.attr('object')
});

App.StandardCreditCardPaymentModel = Em.Object.extend({
    cardOwner: '',
    cardNumber: '',
    expirationMonth: '',
    expirationYear: '',
    cvcCode: '',

    creditcardLengthDict: {
        'Visa': '^[0-9]{13,16}$',
        'MasterCard': '^[0-9]{16,19}$',
        'AmericanExpress': '^[0-9]{15}$',
        'DinersClub': '^[0-9]({14}|{16}$',
        'Discover': '^[0-9]{16}',
        'JCB': '^[0-9]{16}'
    },

    creditcardRegexDict: {
        '^4[0-9].*': 'Visa',
        '^5[1-5].*': 'MasterCard',
        '^3[47].*': 'AmericanExpress',
        '^3(?:0[0-5]|[68][0-9]).*': 'DinersClub',
        '^6(?:011|5[0-9]{2}).*': 'Discover',
        '^(2131|1800|35\d{3}).*': 'JCB'
    },

    // creditCardValidation
    creditcardBrandDetector: function () {

        var cardNumber = this.get('cardNumber');
        for (var key in this.creditcardRegexDict) {
            if (cardNumber.search(key) == 0){
                this.set('creditcard', this.creditcardRegexDict[key]);
            }
        }

    }.observes('cardNumber.length'),

    creditcardLengthVerifier: function () {

        var lengthRegex = this.creditcardLengthDict[this.get('creditcard')];
        var cardNumber = this.get('cardNumber');
        return (cardNumber.search(lengthRegex) == 0);

    }.property('cardNumber.length')

});
