App.DocdataCreditcard = App.StandardCreditCardPaymentModel.extend();

App.DocdataPayment = Em.Object.extend({
    paymentMethod: ''
});

App.DocdataIdeal = App.DocdataPayment.extend({
    default_pm: 'ideal',
    ideal_issuer_id: ''
});

