App.DonationController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {

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

    cleanKommas: function() {
        var amount = this.get('model.amount');
        if (amount.indexOf(",") != -1) {
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

            _this.cleanKommas();

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

            // If the donation is unchanged then move on to the payments modal.
            if (!donation.get('isDirty')) {
                var payment = App.MyOrderPayment.createRecord({order: order});
                
                this.send('modalSlide', 'orderPayment', payment);
            }

            // Set is loading property until success or error response
            _this.set('isBusy', true);

            donation.save().then(
                // Success
                function() {
                    var payment = App.MyOrderPayment.createRecord({order: order});
                    _this.send('modalSlide', 'orderPayment', payment);
                },
                // Failure
                function(){
                     _this.send('modalError');
                     
                    // Handle error message here!
                    _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model')));

                    throw new Em.error('Saving Donation failed!');
                }
            );
        }
    }
});


App.ProjectSupporterListController = Em.ArrayController.extend({
    needs: ['project'],

    model: function () {
        return App.ProjectDonation.find({project: this.get('controllers.project.id')});
    }.property('controllers.project.id'),

    supportersLoaded: function(sender, key) {
        if (this.get(key)) {
            this.set('recentSupporters', this.get('model').toArray().splice(0, 10));
        } else {
            this.set('recentSupporters', null);
        }
    }.observes('model.isLoaded')
});


App.DonationSuccessController = Em.ObjectController.extend({});

// DonationWallPostController extends the TextWallPostNewController as the main
// functionality of the controller is to allow the user to post the the
// project/fundraiser wall.
App.DonationWallPostController = App.TextWallPostNewController.extend(BB.ModalControllerMixin, {
    needs: ['donationSuccess', 'projectIndex', 'fundRaiserIndex'],

    parentType: function(){
        if (this.get('controllers.donationSuccess.fundraiser')) return 'fundraiser';

        return 'project';
    }.property('controllers.donationSuccess.fundraiser'),

    parentId: function(){
        if (this.get('controllers.donationSuccess.fundraiser')) {
            return this.get('controllers.donationSuccess.fundraiser.id');
        }

        return this.get('controllers.donationSuccess.project.id');
    }.property('controllers.donationSuccess.fundraiser.id', 'controllers.donationSuccess.project.id'),

    createNewWallPost: function(){
        var parent_type = this.get('parentType');
        var parent_id = this.get('parentId');
        if (parent_type && parent_id){
            var post = App.TextWallPost.createRecord({
                parent_type: parent_type,
                parent_id: parent_id
            });
            this.set('model', post);
        }
    }.observes('parentType', 'parentId'),

    // Override default _wallPostSuccess method
    _wallPostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallPostList');

        // Add new wallpost to project/fundraiser view
        list.unshiftObject(record);

        // Close modal
        this.send('close');
        this.send('setFlash', gettext("Thanks for your message!"));
    },

    targetType: function () {
        var parentType = this.get('parentType');
        if (!parentType) return null;

        return parentType.match(/project/) ? 'project' : 'fundraiser';
    }.property('parentType'),

    wallPostList: function() {
        var parentType = this.get('parentType');
        
        if (!parentType) return null;
        var indexType = parentType.match(/project/) ? 'controllers.projectIndex.model' : 'controllers.fundRaiserIndex.model';

        return this.get(indexType);
    }.property('parentType'),

    formTitle: function () {
        var parentType = this.get('parentType');
        
        if (parentType == 'fundraiser') return gettext('Leave a message on the fundraiser wall');
        else return gettext('Leave a message on the project wall');
    }.property()
});


