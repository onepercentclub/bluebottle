App.DocdataPayment = Em.Object.extend({
    paymentMethod: ''
});

App.DocdataCreditcard = App.DocdataPayment.extend({
    default_pm: ''
});

App.DocdataIdeal = App.DocdataPayment.extend({
    default_pm: 'ideal',
    ideal_issuer_id: ''
});

