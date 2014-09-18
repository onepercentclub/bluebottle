App.DocdataCreditcardController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm'],

    isVisa: Em.computed.equal('default_pm', 'visa'),
    isMastercard: Em.computed.equal('default_pm', 'mastercard'),

    init: function() {
        this._super();
        this.set('model', App.DocdataCreditcard.create({
            default_pm: 'mastercard'
        }));
    }
});

App.DocdataIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm', 'ideal_issuer_id'],

    init: function () {
        this._super();
        this.set('model', App.DocdataIdeal.create());
    }
});

App.DocdataPaypalController = App.StandardPaymentMethodController.extend({
    init: function () {
        this._super();
        this.set('model', App.DocdataPaypal.create({
            default_pm: 'paypal'
        }));
    }
});

App.DocdataDirectdebitController = App.StandardPaymentMethodController.extend();
