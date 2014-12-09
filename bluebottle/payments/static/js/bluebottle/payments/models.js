App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment_methods',

    provider: DS.attr('string'),
    profile: DS.attr('string'),
    name: DS.attr('string'),

    providerName: function () {
        return this.get('provider').capitalize()
    }.property('provider'),

    uniqueId: function () {
        var profile = this.get('profile');
        if (profile) profile = profile.capitalize();

        return this.get('provider') + profile;
    }.property('provider', 'profile')
});

App.OrderPayment = DS.Model.extend({
    user: DS.belongsTo('App.UserPreview'),
    order: DS.belongsTo('App.MyOrder'),
    status: DS.attr('string', {defaultValue: null}),
    created: DS.attr('date'),
    updated: DS.attr('date'),
    closed: DS.attr('date'),
    amount: DS.attr('number')
});

App.MyOrderPayment = App.OrderPayment.extend({
    url: 'order_payments/my',

    payment_method: DS.attr('string'),
    integrationData: DS.attr('object'),
    authorizationAction: DS.attr('object')
});


App.StandardPaymentModel = Em.Object.extend({

});


App.StandardCreditCardPaymentModel = App.StandardPaymentModel.extend({
    cardOwner: '',
    cardNumber: '',
    expirationMonth: '',
    expirationYear: '',
    cvcCode: '',

    creditcardLengthDict: {
        'visa': '^[0-9]{13,16}$',
        'mastercard': '^[0-9]{16,19}$',
        'americanexpress': '^[0-9]{15}$',
        'dinersclub': '^[0-9]({14}|{16}$',
        'discover': '^[0-9]{16}',
        'jcb': '^[0-9]{16}'
    },

    creditcardRegexDict: {
        '^4[0-9].*': 'visa',
        '^5[1-5].*': 'mastercard',
        '^3[47].*': 'americanexpress',
        '^3(?:0[0-5]|[68][0-9]).*': 'dinersclub',
        '^6(?:011|5[0-9]{2}).*': 'discover',
        '^(2131|1800|35\d{3}).*': 'jcb'
    },

    creditcardBrandDetector: function () {
        var cardNumber = this.get('cardNumber');
        for (var key in this.creditcardRegexDict) {
            if (cardNumber.search(key) === 0){
                return this.creditcardRegexDict[key];
            }
        }
        return null;
    },

    creditcardLengthVerifier: function (brand) {
        var lengthRegex = this.creditcardLengthDict[brand];
        var cardNumber = this.get('cardNumber');
        return (cardNumber.search(lengthRegex) === 0);
    },

    creditcardVerifier: function () {
        this.set('validCreditcard', false);
        this.set('creditcardBrand', this.creditcardBrandDetector());
        this.set('validCreditcard', this.creditcardLengthVerifier(this.get('cardNumber').replace(/ /g,'')));

        this.addWhiteSpacesToCardNumber();
    }.observes('cardNumber.length'),

    addWhiteSpacesToCardNumber: function () {
        var cardNumber = this.get('cardNumber');
        var length = cardNumber.length;
        if (length == 4 || length == 9 || length == 14 || length == 19) {
            this.set('cardNumber', cardNumber + ' ');
        }
    }
});
