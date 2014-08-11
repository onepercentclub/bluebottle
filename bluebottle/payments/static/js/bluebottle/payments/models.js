App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment-methods',

    provider: DS.attr('string'),
    profile: DS.attr('string'),

    name: DS.attr('string'),

    uniqueId: function () {
        if (this.get('provider')) {
            return this.get('provider') + this.get('profile').capitalize();
        }
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

    paymentMethod: DS.belongsTo('App.PaymentMethod'),

    // Hosted payment page details
    integrationDetails: DS.attr('object'),
    integrationData: DS.attr('object')
});

App.StandardCreditCardPaymentModel = Em.Object.extend({
    cardOwner: '',
    cardNumber: '',
    expirationMonth: '',
    expirationYear: '',
    cvcCode: ''
});
