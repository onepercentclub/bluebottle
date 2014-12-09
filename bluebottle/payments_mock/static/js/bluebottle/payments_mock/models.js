App.MockPayment = Em.Object.extend({
    paymentMethod: ''
});

App.MockCreditcard = App.MockPayment.extend({
    default_pm: ''
});

App.MockiDeal = App.MockPayment.extend({
    default_pm: 'ideal',
    ideal_issuer_id: ''
});

App.MockPal = App.MockPayment.extend({
    default_pm: 'paypal'
});