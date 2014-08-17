App.DocdataCreditcardController = App.StandardCreditCardPaymentController.extend({
    init: function() {
        this._super();
        this.set('model', App.DocdataCreditcard.create());
    },

    getIntegrationData: function() {
        return {encryptedData: 'atadcoD123'};
    }
});

App.DocdataIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['issuerId'],

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
