App.PaymentController = Em.ObjectController.extend(App.ControllerValidationMixin,{
    needs: ['application', 'creditcard', 'paypal'],

    preFixedProfileId: function() {
        return 'tab' + this.get('profile');
    }.property('profile'),

    preFixedProfileContentId: function() {
        return 'tab-content' + this.get('profile');
    }.property('profile'),

    validCardName: function() {
        debugger
    }.property('model.cardOwner'),

    willOpen: function () {
        var _this = this,
            controller = this.get('controller'),
            payment = this.get('model');

        // TODO: we need to send the amount associated with the payment as this
        //       will determine the payment methods. Also, in the future we will
        //       need to send the country with the amount.
        App.PaymentMethod.find().then(
            // Success
            function(methods) {
                _this.set('methods', methods);
            },
            // Failure
            function(methods) {
                throw new Em.error('Fetching PaymentMethod\'s failed!');
            }
        );
    },

    _processPaymentMetadata: function () {
        // integration_url (at PSP)
        // integration_method (GET/POST/PUT)
        // integration_payload (optional metadata required by PSP)
        // integration_type (redirect/popup)
        var meta = this.get('model.integrationDetails');
        if (meta.type == 'redirect') {
            if (meta.method == 'get') {
              var getUrl = this._buildUrl(meta.url, meta.payload);

              window.location.replace(getUrl);
            }
        }
    },

    _buildUrl: function (url, parameters){
        var qs = '';

        for(var key in parameters) {
            var value = parameters[key];
            qs += encodeURIComponent(key) + '=' + encodeURIComponent(value) + '&';
        }
        
        if (qs.length > 0) {
            qs = qs.substring(0, qs.length-1);
            url = url + '?' + qs;
        }

        return url;
    },

    actions: {
        nextStep: function () {
            var _this = this,
                payment = this.get('model');
            payment.save().then(
                // Success
                function (payment) {
                    // Reload the order to receive any backend updates to the order status
                    // NOTE: when using the mock api we will need to manually set the order
                    //       status here.
                    payment.get('order').then(function (order) {
                        order.reload();
                    });

                    // Proceed to the next step based on the status of the payment
                    // 1) Payment status is 'success'
                    // 2) Payment status is 'in_progress'

                    if (payment.get('success')) {
                        // Load the success modal
                        // Since all models are already loaded in Ember here, we should just be able
                        // to get the first donation of the order here
                        var donation = payment.get('order.donations').objectAt(0);
                        _this.send('modalSlide', 'donationSuccess', donation);
                    } else {
                        _this._processPaymentMetadata();
                    }
                },
                // Failure
                function (payment) {

                }
            );
        },

        selectedPaymentMethod: function(paymentMethod) {
            this.set('currentPaymentMethod', paymentMethod);
            debugger
            var applicationRoute = App.__container__.lookup('route:application');
            applicationRoute.render(this.get('currentPaymentMethod.uniqueId'), {
                into: 'payment',
                outlet: 'paymentMethod'
            });
        }
    }
});

App.CreditcardController = Em.ObjectController.extend(App.ControllerValidationMixin, {

    fieldsToWatch: ['cardOwner', 'cardNumber', 'expirationMonth', 'expirationYear', 'cvcCode'],
    requiredFields: ['cardOwner', 'cardNumber', 'expirationMonth', 'expirationYear', 'cvcCode'],

    creditcardDict: //change
        [{ 'cardName': 'Visa', 'regex': '^4[0-9]{6,}$', 'image': 'path'},
        { 'cardName': 'MasterCard', 'regex': '^5[1-5][0-9]{5,}$', 'image': 'path'},
        { 'cardName': 'AmericanExpress', 'regex': '^3[47][0-9]{5,}$', 'image': 'path'},
        { 'cardName': 'DinersClub', 'regex': '^3(?:0[0-5]|[68][0-9])[0-9]{4,}$', 'image': 'path'},
        { 'cardName': 'Discover', 'regex': '^6(?:011|5[0-9]{2})[0-9]{3,}$', 'image': 'path'},
        { 'cardName': 'JCB', 'regex': '^(?:2131|1800|35[0-9]{3})[0-9]{3,}$', 'image': 'path'}],


    // creditCardValidation
    creditCardDetector: function(){


    }.property('cardNumber.length'),

    init: function() {
        this._super();
        this.set('errorDefinitions', [
            {
                'property': 'cardOwner',
                'validateProperty': 'validCardOwner',
                'message': gettext('Card Owner can\'t be left empty'),
                'priority': 2
            },
            {
                'property': 'cardNumber',
                'validateProperty': 'validCardNumber',
                'message': gettext('This card number is not valid'),
                'priority': 1
            }
        ]);
        debugger
        this.set('model', App.CreditcardModel.createRecord({}));
        this.enableValidation();
        this.set('validationErrors', this.validateErrors(this.get('errorDefinitions'), this.get('model')));
//            cardOwner: '',
//            cardNumber: '',
//            expirationMonth: '',
//            expirationYear: '',
//            cvcCode: ''
//
//        }));
    }

})



App.PaymentMetaDataController = Em.ObjectController.extend({

});