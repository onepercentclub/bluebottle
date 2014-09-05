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


App.DocdataDirectdebitController = App.StandardPaymentMethodController.extend({
    requiredFields: ['iban', 'bic', 'accountName', 'accountCity', 'agree'],

    bicHelp: function(){
        var bic = '';
        var bank = this.get('iban').substring(4,8);
        switch (bank) {
            case 'ABNA':
                bic = 'ABNANL2A';
                break;
            case 'AEGO':
                bic = 'AEGONL2U';
                break;
            case 'INGB':
                bic = 'INGBNL2A';
                break;
            case 'RABO':
                bic = 'RABONL2U';
                break;
            case 'SNSB':
                bic = 'SNSBNL2A';
                break;
            case 'ASN':
                bic = 'ASNBNL21';
                break;
            case 'FVLB':
                bic = 'FVLBNL22';
                break;
            case 'KNAB':
                bic = 'KNABNL2H';
                break;
            case 'TRIO':
                bic = 'TRIONL2U';
                break;
        }
        if (bic) {
            this.set('bic', bic);
        }

    }.observes('iban'),

    init: function () {
        var user = this.get('currentUser');
        this.set('model', App.DocdataDirectdebit.create());
        if (user) {
            this.set('model.account_name', user.get('full_name'));
        }
        this._super();
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
