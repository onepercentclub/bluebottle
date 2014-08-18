App.MollieIdealController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {
    requiredFields: ['issuer'],
    issuer: null,
    init: function() {
        this._super();
        this.set('model', App.MollieIdeal.create());
    },
    getIntegrationData: function() {
        return {'issuer': this.get('issuer.id')};
    }


});
