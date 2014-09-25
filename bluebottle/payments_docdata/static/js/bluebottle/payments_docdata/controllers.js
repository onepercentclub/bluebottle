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
        this.set('model', App.DocdataIdeal.create({
            default_pm: 'ideal'}
        ));

        this.set('errorDefinitions', [
            {
                'property': 'ideal_issuer_id',
                'validateProperty': 'ideal_issuer_id',
                'message': gettext('You must select a bank'),
                'priority': 1
            }
        ]);
    },

    getIntegrationData: function() {
        // If there are no errors, error properties should be removed from the model

        var model = this.get('model');
        model.set('allErrors', undefined);
        model.set('allError', undefined);
        model.set('validationErrors', undefined);
        model.set('errorList', undefined);
        
        return model;
    },
    
    // returns a list of two values [validateErrors, errorsFixed]
    validateFields: function () {
        // Enable the validation of errors on fields only after pressing the signup button
        this.enableValidation();

        // Clear the errors fixed message
        this.set('errorsFixed', false);

        // Ignoring API errors here, we are passing ignoreApiErrors=true
        return [this.validateErrors(this.get('errorDefinitions'), this.get('model'), true), this.get('errorsFixed')];
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
