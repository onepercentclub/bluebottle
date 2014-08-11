App.PaymentController = Em.ObjectController.extend({
    needs: ['application'],

    errorsFixedBinding: 'paymentMethodController.errorsFixed',
    validationErrorsBinding: 'paymentMethodController.validationErrors',
    isBusyBinding: 'paymentMethodController.isBusy',

    // Override modal willOpen handler to fetch the payment methods
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
        // This function will handle where to direct the user after they submit the
        // payment selection. It handles the step based on these properties returned
        // by the server when they submitted the purchase:
        //    integration_url (at PSP)
        //    integration_method (GET/POST/PUT)
        //    integration_payload (optional metadata required by PSP)
        //    integration_type (redirect/popup)
        var meta = this.get('model.integrationDetails');
        if (meta.type == 'redirect') {
            if (meta.method == 'get') {
              var getUrl = this._buildUrl(meta.url, meta.payload);

              window.location.replace(getUrl);
            }
        }
    },

    // Process the data associated with the current payment method
    _setIntegrationData: function () {
        var paymentMethodController = this.get('paymentMethodController');

        if (paymentMethodController) {
            var integrationData = paymentMethodController.getIntegrationData();
            this.set('integrationData', integrationData);
        }
    },

    _buildUrl: function (url, parameters) {
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

    // Set the current payment method controller based on selected method
    _setPaymentMethodController: function () {
        var method = this.get('payment_method');
        if (!method) return;

        this.set('paymentMethodController', this.container.lookup('controller:' + this.get('payment_method').get('uniqueId')));
    }.observes('payment_method'),

    actions: {
        previousStep: function () {
            // Slide back to the donation modal - keeping the current donation.
            // Currently the there is only one donation associated with each order
            // so grab the first donation item.
            var donation = this.get('model.order.donations').objectAt(0);
            this.send('modalSlideBack', 'donation', donation);
        },

        nextStep: function () {
            var _this = this,
                payment = this.get('model');

            // check for validation errors generated in the current payment method controller
            this.get('paymentMethodController').validateFields();

            // Check client side errors
            if (this.get('validationErrors')) {
                this.send('modalError');
                return false;
            }

            // Set is loading property until success or error response
            _this.set('isBusy', true);
            
            // Set the integration data coming from the current payment method controller
            this._setIntegrationData();

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

                    // FIXME: For testing purposes we will direct the user to the success
                    //        modal for creditcard payments and to the mock service provider
                    //        for all others.
                    if (this.get('payment_method.profile') == 'creditcard') {
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
            // Set the payment method on the payment model
            this.set('payment_method', paymentMethod);

            // Render the payment method view
            var applicationRoute = App.__container__.lookup('route:application');
            applicationRoute.render(this.get('payment_method').get('uniqueId'), {
                into: 'payment',
                outlet: 'paymentMethod'
            });
        }
    }
});

/*
 * Some standard controllers which can be extended for different payment service providers
 */

App.StandardPaymentMethodController = Em.ObjectController.extend({
    getIntegrationData: function() {
        //override me
        return null;
    },

    validateFields: function () {
        return null;
    }
});

App.StandardCreditCardPaymentController = App.StandardPaymentMethodController.extend(App.ControllerValidationMixin, {
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

    validateFields: function () {
        // Enable the validation of errors on fields only after pressing the signup button
        this.enableValidation();

        // Clear the errors fixed message
        this.set('errorsFixed', false);

        // Ignoring API errors here, we are passing ignoreApiErrors=true
        this.set('validationErrors', this.validateErrors(this.get('errorDefinitions'), this.get('model'), true));
    },

    init: function() {
        this._super();
        this.set('errorDefinitions', [
            {
                'property': 'cardOwner',
                'validateProperty': 'cardOwner.length',
                'message': gettext('Card Owner can\'t be left empty'),
                'priority': 1
            },
            {
                'property': 'cardNumber',
                'validateProperty': /\d{16}/,
                'message': gettext('This card number is not valid'),
                'priority': 2
            },
            {
                'property': 'expirationMonth',
                'validateProperty': /^1[0-2]$|^0[1-9]$/,
                'message': gettext('The expiration month is not valid'),
                'priority': 3
            },
            {
                'property': 'expirationYear',
                'validateProperty': /^[1-9]\d{1}$/,
                'message': gettext('The expiration year is not valid'),
                'priority': 4
            },
            {
                'property': 'cvcCode',
                'validateProperty': /^\d{3}$/,
                'message': gettext('The CVC is not valid'),
                'priority': 5
            }
        ]);
    }
});