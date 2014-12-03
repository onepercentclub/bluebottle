App.DocdataCreditcardController = App.StandardPaymentMethodController.extend({
    cardTypes:  [
        {'id':'amex', 'name': 'American Express'},
        {'id':'visa', 'name': 'Visa Card'},
        {'id':'mastercard', 'name': 'Master Card'},
    ],
    requiredFields: ['default_pm'],
    errorDefinitions: [
        {
                'property': 'default_pm',
                'validateProperty': 'default_pm.length',
                'message': gettext('Select a credit card'),
                'priority': 1
        }
    ],
    promptText: gettext("Select your credit card"), 

    init: function() {
        this._super();
        this._clearModel();
    },

    _clearModel: function () {
        this.set('model', App.DocdataCreditcard.create({
            default_pm: ''
        }));
    },

    actions: {
        selectCardType: function (cardType) {
            if ($.inArray(cardType, this.get('cardTypes')) > -1) {
                this.set('model.default_pm', cardType.id);
            }
        }
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
    requiredFields: ['iban', 'bic', 'account_name', 'account_city', 'agree'],
    didChange: false,
    
    accountNamePlaceholder: function() {
        return gettext("Your account name");
    }.property(),

    _clearModel: function() {
        var user = this.get('currentUser');
        this.set('model', App.DocdataDirectdebit.create());
        if (user) {
            this.set('model.account_name', user.get('full_name'));
        }
    },

    errorDefinitions: [
        {
            'property': 'account_name',
            'validateProperty': 'account_name.length',
            'message': gettext('Please fill in your account name'),
            'priority': 1
        },
        {
            'property': 'iban',
            'validateProperty': 'iban.length',
            'message': gettext('Please fill in your IBAN number'),
            'priority': 2
        },
        {
            'property': 'bic',
            'validateProperty': 'bic.length',
            'message': gettext('Please fill in your BIC/SWIFT code'),
            'priority': 3
        },
        {
            'property': 'agree',
            'validateProperty': 'agree',
            'message': gettext('Please agree to the amount being withdrawn from your account'),
            'priority': 4
        }
    ],

    _fieldChanged: function() {
        this.set('didChange', true);
    }.observes('iban', 'bic', 'account_name', 'agree'),

    bicHelp: function(){
        var bic = '',
            iban = this.get('iban').toUpperCase(),
            bank = iban.substring(4,8);

        // Iban to upper
        this.set('iban', iban);
        // Lookup Bic based on Iban
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
        this._super();

        this._clearModel();
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
