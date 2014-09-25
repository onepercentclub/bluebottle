App.DocdataCreditcardController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm'],
    errorDefinitions: [
        {
                'property': 'default_pm',
                'validateProperty': 'default_pm.length',
                'message': gettext('Select a credit card'),
                'priority': 1
        }
    ],


    init: function() {
        this._super();
        this._clearModel();
    },

    _clearModel: function () {
        this.set('model', App.DocdataCreditcard.create({
            default_pm: ''
        }));
    }
});

App.DocdataIdealController = App.StandardPaymentMethodController.extend({
    requiredFields: ['default_pm', 'ideal_issuer_id'],
    errorDefinitions: [
        {
            'property': 'ideal_issuer_id',
            'validateProperty': 'ideal_issuer_id.length',
            'message': gettext('Select your bank'),
            'priority': 1
        }
    ],

    init: function () {
        this._super();
        this.set('model', App.DocdataIdeal.create());
    }
});

App.DocdataPaypalController = App.StandardPaymentMethodController.extend({
    // Ignore client-side validations as the form doesn't need user input
    blockingErrors: false,
    clientSideValidationErrors: Em.K,

    init: function () {
        this._super();
        this.set('model', App.DocdataPaypal.create({
            default_pm: 'paypal'
        }));
    }
});

App.DocdataDirectdebitController = App.StandardPaymentMethodController.extend();
