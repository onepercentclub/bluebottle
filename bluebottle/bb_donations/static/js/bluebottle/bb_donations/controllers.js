App.DonationController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, App.SaveDonationMixin, {
    requiredFields: ['amount' ],
    fieldsToWatch: ['amount' ],
    defaultAmounts: [50, 75, 100],

    init: function() {
        this._super();

        this.set('errorDefinitions', [
             {
                'property': 'amount',
                'validateProperty': 'validAmount',
                'message': gettext('C\'mon, don\'t be silly! Give them at least 5 euro'),
                'priority': 1
            },
        ]);
    },

	willOpen: function() {
        this.container.lookup('controller:modalContainer').set('type', 'big-modal donation-small');
    },

    willClose: function() {
        this.container.lookup('controller:modalContainer').set('type', 'big-modal donation');
    },

    cleanCommas: function() {
        var amount = this.get('model.amount');
        if (typeof amount == 'string' && amount.indexOf(",") != -1) {
            this.set('amount', amount.replace(",", "."));
        }
        return;

    },

    actions: {
        changeAmount: function(amount){
            this.set('amount', amount);
        },

        nextStep: function(){
            var _this = this,
                donation = this.get('model'),
                order = donation.get('order');

            _this.cleanCommas();

            // Enable the validation of errors on fields only after pressing the signup button
            _this.enableValidation();

            // Clear the errors fixed message
            _this.set('errorsFixed', false);

            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                this.send('modalError');

                return false;
            }

            if (this.get('currentUser.isAuthenticated')) {
                _this._saveDonation();
            } else {
                _this.send('modalSlideLeft', 'orderSignup');
            }
        }
    }
});

App.DonationSuccessController = Em.ObjectController.extend(BB.ModalControllerMixin, {});


App.MyDonationListController = Em.ArrayController.extend({
    page: 1,
    canLoadMore: function(){
        if (this.get('length') < this.get('meta.total')){
            return true;
        }
        return false;
    }.property('length', 'meta.total'),

    actions: {
        loadMore: function(){
            var _this = this;
            if (this.get('canLoadMore')) {
                this.incrementProperty('page');
                App.MyDonation.find({status: ['success', 'pending'], page: this.get('page')}).then(function(items){
                    _this.pushObjects(items.toArray());
                });

            }
        }
    }

});
