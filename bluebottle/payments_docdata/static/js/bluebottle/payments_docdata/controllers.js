App.DocdataCreditcardController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm'],

    init: function() {
        this._super();
        this.set('model', App.DocdataCreditcard.create());
    }
});

App.DocdataIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm', 'ideal_issuer_id'],

    init: function () {
        this._super();
        this.set('model', App.DocdataIdeal.create());
    }
});

App.DocdataPaypalController = App.StandardPaymentMethodController.extend();
App.DocdataDirectdebitController = App.StandardPaymentMethodController.extend();
