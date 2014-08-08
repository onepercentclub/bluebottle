App.DonationController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {

    requiredFields: ['amount' ],
    fieldsToWatch: ['amount' ],

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


    actions: {
        changeAmount: function(amount){
            this.set('amount', amount);
        },

        nextStep: function(){
            var _this = this,
                donation = this.get('model'),
                order = donation.get('order');

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

            // Set is loading property until success or error response
            _this.set('isBusy', true);

            donation.save().then(
                // Success
                function() {
                    var payment = App.MyPayment.createRecord({order: order});
                    _this.send('modalSlide', 'payment', payment);
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

    supporters: function () {
        return App.ProjectDonation.find({project: this.get('controllers.project.id')});
    }.property('controllers.project.id'),

    supportersLoaded: function(sender, key) {
        if (this.get(key)) {
            this.set('model', this.get('supporters').toArray());
        } else {
            this.set('model', null);
        }
    }.observes('supporters.isLoaded')
});


App.DonationSuccessController = Em.ObjectController.extend({});

// DonationWallPostController extends the TextWallPostNewController as the main
// functionality of the controller is to allow the user to post the the
// project/fundraiser wall.
App.DonationWallPostController = App.TextWallPostNewController.extend(BB.ModalControllerMixin, {
    needs: ['donationSuccess', 'projectIndex', 'fundRaiserIndex'],

    parentType: function(){
        if (this.get('controllers.donationSuccess.fundRaiser')) return 'fundRaiser';
        return 'project';
    }.property('controllers.donationSuccess.fundRaiser'),

    parentId: function(){
        if (this.get('controllers.donationSuccess.fundRaiser')) {
            return this.get('controllers.donationSuccess.fundRaiser.id');
        }
        return this.get('controllers.donationSuccess.project.id');
    }.property('controllers.donationSuccess.fundRaiser.id', 'controllers.donationSuccess.project.id'),

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

    _wallPostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallPostList');

        list.unshiftObject(record);
        this.send('close');
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
    }.property('parentType')
});


