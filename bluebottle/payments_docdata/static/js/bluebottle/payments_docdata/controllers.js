App.DocdataCreditcardController = App.StandardCreditCardPaymentController.extend({
    init: function() {
        this._super();
        this.set('model', App.DocdataCreditcard.create());
    },

    getIntegrationData: function() {
        return {encryptedData: 'atadcoD123'};
    }
});

App.DocdataPaypalController = Em.Controller.extend();
App.DocdataIdealController = Em.Controller.extend();
App.DocdataDirectdebitController = Em.Controller.extend();
App.DocdataWebmenuController = Em.Controller.extend();
