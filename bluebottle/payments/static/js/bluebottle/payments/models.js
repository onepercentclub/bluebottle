if (DEBUG) {
    App.Store.registerAdapter("App.PaymentMethod", App.MockAdapter);
    App.Store.registerAdapter("App.Payment", App.MockAdapter);
    App.Store.registerAdapter("App.MyPayment", App.MockAdapter);
}

App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment-methods',

    provider: DS.attr('string'),
    name: DS.attr('string'),
    profile: DS.attr('string')
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
    integrationDetails: DS.attr('integrationObject')
});
