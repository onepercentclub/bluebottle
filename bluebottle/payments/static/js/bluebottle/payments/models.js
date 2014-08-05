if (DEBUG) {
    App.Store.registerAdapter("App.PaymentMethod", App.MockAdapter);
}

App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment-methods',
    provider: DS.attr('string'),
    name: DS.attr('string'),
    profile: DS.attr('string')
});