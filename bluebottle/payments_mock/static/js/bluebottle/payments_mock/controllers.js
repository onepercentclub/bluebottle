App.MockIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['issuerId'],

    init: function() {
        this._super();
        
        this.set('errorDefinitions', [
            {
                'property': 'issuerId',
                'validateProperty': 'issuerId.length',
                'message': gettext('Select your bank'),
                'priority': 1
            }
        ]);
        this.set('model', App.MockiDeal.create());
    }

});

App.MockPaypalController = App.StandardPaymentMethodController.extend({
    getIntegrationData: function(){
        return {};
    }
});

App.MockCreditcardController = App.StandardPaymentMethodController.extend({
    init: function() {
        this._super();
        this.set('model', App.MockCreditcard.create());
    },

    getIntegrationData: function(){
        return {};
    }
});