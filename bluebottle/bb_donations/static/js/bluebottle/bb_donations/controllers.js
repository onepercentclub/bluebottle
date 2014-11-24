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

    _hideWallPostMessage: function() {
        $(".wallpost-message-area").hide();
    },

    _showWallPostMessage: function() {
        $(".wallpost-message-area").show();
    },

    actions: {
        saveWallPost: function() {
            var controller = this,
                parent_type = this.get('parentType'),
                parent_id = this.get('parentId'),
                wallPost = this.get('model');

            if (Em.isEmpty(this.get('text'))) {
                this.send('modalError');
                this.set('error', gettext('Perhaps you should try typing something'));
            }

            controller._hideWallPostMessage();

            if (parent_type && parent_id) {
                wallPost.set('parent_id', parent_id);
                wallPost.set('parent_type', parent_type);
            }
            wallPost.set('type', 'text');

            wallPost.save().then(function (record) {
                controller._wallPostSuccess(record);
            }, function (record) {
                controller._showWallPostMessage();
                controller.set('error', record.get('error'));
            });
        },

    },

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
