App.MockIdealController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {
    requiredFields: ['issuerId'],

    init: function() {
        this._super();
        this.set('model', App.MockIdeal.create());
    }

});
