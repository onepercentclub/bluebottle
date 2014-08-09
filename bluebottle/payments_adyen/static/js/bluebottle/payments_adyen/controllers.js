App.AdyenCreditcardController = App.StandardCreditCardPaymentController.extend({

    init: function() {
        this._super();
        this.set('model', App.AdyenCreditcard.create());
    },

    getIntegrationData: function() {
        return {encryptedData: 'neydA123'};
    }

});

App.AdyenIdealController = Em.Controller.extend();
App.AdyenPaypalController = Em.Controller.extend();
