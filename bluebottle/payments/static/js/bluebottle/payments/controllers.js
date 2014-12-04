App.OrderPaymentController = Em.ObjectController.extend({
    needs: ['application', 'projectDonationList', 'fundraiserDonationList'],

    errorsFixedBinding: 'paymentMethodController.errorsFixed',
    validationErrorsBinding: 'paymentMethodController.validationErrors',
    blockingErrorsBinding: 'paymentMethodController.blockingErrors',
    isBusyBinding: 'paymentMethodController.isBusy',
    currentPaymentMethod: null,
    methods: null,

    currentPaymentMethodURL: function() {
        return 'http://www.' + this.get('currentPaymentMethod.provider') + '.com';
    }.property('currentPaymentMethod.provider'),

    // Override modal willOpen handler to fetch the payment methods
    willOpen: function () {
        var _this = this;

        App.PaymentMethod.find().then(
            // Success
            function(methods) {
                _this.set('methods', methods);
                // Also explicitely reload the payment method tab when the methods are fetched. This is required
                // when the user closes and reopens the modal. 
                _this._setPaymentMethodController();
            },
            // Failure
            function(methods) {
                throw new Em.error('Fetching PaymentMethod\'s failed!');
            }
        );
    },

    // resetCurrentPaymentMethod sets a payment method on the order payment using the payment method of the previously
    // failed payment. 
    _resetCurrentPaymentMethod: function() {
        if (!this.get('payment_method')) return;
        
        var methods = this.get('methods'),
            currentItem = methods.objectAt(methods.get('length') - 1);

        if (currentItem && typeof this.get('payment_method') == 'string' &&  currentItem.get('uniqueId') == this.get('payment_method')) {
            this.set('currentPaymentMethod', currentItem);
        }
    }.observes('methods.@each.name'),

    willClose: function () {
        var currentPaymentMethodController = this.get('paymentMethodController');
        if (currentPaymentMethodController) {
            currentPaymentMethodController.clearValidations();
            currentPaymentMethodController._clearModel();
        }
    },

    didError: function () {
        if (this.get('validationErrors')) {
            // Error set so not busy anymore
            this.set('isBusy', false);

            // Call error action on the modal
            this.send('modalError');
        }
    }.observes('validationErrors'),

    _setFirstPaymentMethod: function () {
        if (this.get('methods.length') && !this.get('currentPaymentMethod') && !this.get('payment_method')) {
            this.set('currentPaymentMethod', this.get('methods.firstObject'));
        }
    }.observes('methods.length'),

    _processAuthorizationAction: function () {
        // This function will handle where to direct the user after they submit the
        // payment selection. It handles the step based on these properties returned
        // by the server when they submitted the purchase:
        //    integration_url (at PSP)
        //    integration_method (GET/POST/PUT)
        //    integration_payload (optional metadata required by PSP)
        //    integration_type (redirect/popup)
        var meta = this.get('model.authorizationAction');
        if (meta.type == 'redirect') {
            if (meta.method == 'get') {
                window.location = meta.url;
            }
        }
        if (meta.type == 'success') {
            // Refresh project and donations
            var donation = this.get('order.donations.firstObject');
            // TODO: Refresh Fundraiser if it's a FundRaisser
            // TODO: Refresh donation list
            donation.get('project.getProject').reload();

            this.send('modalFlip', 'donationSuccess', donation, 'modalBack');
        }
    },

    _paymentMethodChanged: function() {
        if (this.get('paymentMethodController.didChange') && ! this.get('isValid')) {
            this.get('model').transitionTo('loaded.created.uncommitted');
        }
    }.observes('paymentMethodController.didChange'),

    // Process the data associated with the current payment method
    _setIntegrationData: function () {
        var paymentMethodController = this.get('paymentMethodController');

        // TODO: How we handle the payment details will depend on the PSP.
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
        var method = this.get('currentPaymentMethod'),
            methodId = this.get('currentPaymentMethod.uniqueId'),
            currentPaymentMethodController = this.get('paymentMethodController');

        if (!methodId) return;

        // Clear the validations on the current payment method controller
        if (currentPaymentMethodController) currentPaymentMethodController.clearValidations();
        
        // Render the payment method view
        var applicationRoute = this.container.lookup('route:application'),
            paymentMethodController = this.container.lookup('controller:' + methodId);

        applicationRoute.render(methodId, {
            into: 'orderPayment',
            outlet: 'paymentMethod'
        });

        // Validations should be initially disabled
        paymentMethodController.disableValidation();

        // Set the payment method controller
        this.set('paymentMethodController', paymentMethodController);

        // Set paymentMethod on the payment based on the currentPaymentMethod
        this.set('payment_method', methodId);
    }.observes('currentPaymentMethod'),

    actions: {
        previousStep: function () {
            // Slide back to the donation modal - keeping the current donation.
            // Currently the there is only one donation associated with each order
            // so grab the first donation item.
            var donation = this.get('model.order.donations.firstObject');
            this.send('modalSlide', 'donation', donation);
        },

        nextStep: function () {
            var _this = this,
                payment = this.get('model');


            // check for validation errors generated in the current payment method controller
            // This call will set the 'validationErrors' property on the payment methods 
            // controller.
            this.get('paymentMethodController').clientSideValidationErrors();

            // Set the property to false so that if the save below fails then user changes to
            // the paymentMethod data will trigger the _paymentMethodChanged in this controller.
            this.set('paymentMethodController.didChange', false);

            // Check client side errors - there is a binding between validationErrors on the 
            // PaymentController and the PaymentMethodController.
            if (this.get('validationErrors')) {
                return false;
            }

            // Set the integration data coming from the current payment method controller
            this._setIntegrationData();

            // Set is loading property until success or error response
            this.set('isBusy', true);

            payment.save().then(
                // Success
                function (payment) {
                    // Reload the order to receive any backend updates to the
                    // order status
                    var order = payment.get('order');
                    order.reload().then(function(reloadedOrder) {
                        // Proceed to the next step based on the status of the payment
                        // 1) Payment status is 'success'
                        // 2) Payment status is 'in_progress'

                        // FIXME: For testing purposes we will direct the user to
                        //        the success modal for creditcard payments and to
                        //        the mock service provider for all others.
                        if (reloadedOrder.get('status') == 'success' || reloadedOrder.get('status') == 'pending') {
                            // Redirect to the order route.
                            _this.transitionToRoute('order', reloadedOrder);
                        } else {
                            // Process the authorization action to determine next
                            // step in payment process.
                            _this._processAuthorizationAction();
                        }
                    });
                },
                // Failure
                function (payment) {
                    _this.set('isBusy', false);
                }
            );

        },

        selectedPaymentMethod: function(paymentMethod) {
            // Set the payment method on the payment model
            this.set('currentPaymentMethod', paymentMethod);
        }
    }
});

/*
 * Some standard controllers which can be extended for different payment service providers
 */

App.StandardPaymentMethodController = Em.ObjectController.extend(App.ControllerValidationMixin, {
    requiredFields: [],
    errorDefinitions: [],
    isBusy: null,
    _clearModel: Em.K,
    didChange: false,

    getIntegrationData: function() {
        return this.get('model');
    }
});

App.StandardCreditCardPaymentController = App.StandardPaymentMethodController.extend({
    cardTypes: ['amex', 'mastercard', 'visa'],
    requiredFields: ['cardOwner', 'cardNumber', 'expirationMonth', 'expirationYear', 'cvcCode'],
    errorDefinitions: [
        {
            'property': 'cardOwner',
            'validateProperty': 'cardOwner.length',
            'message': gettext('Card Owner can\'t be left empty'),
            'priority': 2
        },
        {
            'property': 'cardNumber',
            'validateProperty': 'validCreditcard',
            'message': gettext('Your creditcard doesn\'t have the right number of digit.'),
            'priority': 1
        },
        {
            'property': 'expirationMonth',
            'validateProperty': /^1[02]$|^0[1-9]$/,
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
    ]
});
