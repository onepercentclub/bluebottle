App.DonationModalController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {

    requiredFields: ['amount' ],
    fieldsToWatch: ['amount' ],

    init: function() {
        this._super();

        this.set('errorDefinitions', [
             {
                'property': 'amount',
                'validateProperty': 'validAmount',
                'message': gettext('The amount you donate has to be a number higher than 20'),
                'priority': 1
            },
        ]);
    },


    actions: {
        changeAmount: function(amount){
            debugger
            if (amount != "") {
                this.set('amount', amount);
            } else {
                this.set('amount', null);
            }
        },
        nextStep: function(){

            var _this = this

            // Enable the validation of errors on fields only after pressing the signup button
            _this.enableValidation();

            // Clear the errors fixed message
            _this.set('errorsFixed', false);

            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                this.send('modalError');
                return false
            }

            // Set is loading property until success or error response
            _this.set('isBusy', true);

            var donation = _this.get('model');
            debugger
            donation.save().then(
                // Success
                function(){
                    // Register the successful regular signup with Mixpanel
                    if (_this.get('tracker')) {
                        _this.get('tracker').trackEvent("Donation", {"type": "regular"});
                    }

                    // Call the loadNextTransition in case the user was unauthenticated and was
                    // shown the sign in / up modal then they should transition to the requests route
                    _this.send('loadNextTransition', null);

                    // Close the modal
                    _this.send('close');
                    debugger
                    alert('Saved!');
                },
                // Failure
                function(){
                     _this.send('modalError');
                    // Handle error message here!
                    _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model')));


                }
            )
        }
    }

});