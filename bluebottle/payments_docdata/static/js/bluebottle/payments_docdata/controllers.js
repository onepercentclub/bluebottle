App.DocdataCreditcardController = App.StandardCreditCardPaymentController.extend({
    init: function() {
        this._super();
        this.set('model', App.DocdataCreditcard.create());
    }
});

App.DocdataIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['ideal_issuer_id'],

    init: function () {
        this._super();
        this.set('model', App.DocdataIdeal.create());
    },
    getIntegrationData: function() {
        return this.get('model');
    }
});

App.DocdataPaypalController = App.StandardPaymentMethodController.extend();
App.DocdataDirectdebitController = App.StandardPaymentMethodController.extend();
