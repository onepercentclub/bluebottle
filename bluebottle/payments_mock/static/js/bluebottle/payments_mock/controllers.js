App.MockIdealController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {
    requiredFields: ['issuerId'],

    init: function() {
        this._super();
        this.set('model', App.MockIdeal.create());
    }

});

App.MockPaypalController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {

});

App.MockCreditcardController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {
    init: function() {
        this._super();
        this.set('model', App.MockCreditcard.create());
    },

    getIntegrationData: function(){
        return this.get('model');
    }
});