App.PaymentMethod = DS.Model.extend({
    url: 'payments/payment-methods',
    provider: DS.attr('string'),
    name: DS.attr('string'),
    profile: DS.attr('string')
});