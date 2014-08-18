App.DocdataCreditcard = App.StandardCreditCardPaymentModel.extend();

App.DocdataPayment = Em.Object.extend({
    paymentMethod: ''
});

App.DocdataIdeal = App.DocdataPayment.extend({
    paymentMethod: 'ideal',
    ideal_issuer_id: ''
});

