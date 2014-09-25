App.DocdataPayment = Em.Object.extend({
    paymentMethod: ''
});

App.DocdataCreditcard = App.DocdataPayment.extend({
    default_pm: '',

    isCardSelected: Em.computed.match('default_pm', /[a-z|_]+/i )
});

App.DocdataIdeal = App.DocdataPayment.extend({
    default_pm: 'ideal',
    ideal_issuer_id: ''
});

App.DocdataPaypal = App.DocdataPayment.extend({
    default_pm: 'paypal'
});

