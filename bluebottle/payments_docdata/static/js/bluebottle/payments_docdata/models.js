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


App.DocdataDirectdebit = App.DocdataPayment.extend({
    default_pm: 'direct_debit',
    iban: '',
    bic: '',
    account_name: '',
    account_city: 'Unknown',
    agree: false
});

App.DocdataPaypal = App.DocdataPayment.extend({
    default_pm: 'paypal'
});

