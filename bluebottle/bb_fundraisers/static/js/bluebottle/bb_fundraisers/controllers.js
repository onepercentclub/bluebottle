App.FundraiserIsOwner = Em.Mixin.create({
    isOwner: function() {
        var username = this.get('currentUser.username');
        var ownername = this.get('model.owner.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('model.owner', 'currentUser.username')
});


App.FundraiserController = Em.ObjectController.extend(App.FundraiserIsOwner, {
    needs: ['project'],

    _setDonations: function () {
        if (this.get('isLoaded')) {
            this.set('fundraiserDonations', App.ProjectDonation.find({fundraiser: this.get('id')}));
        }
    }.observes('isLoaded'),
});


App.FundraiserNewController = Em.ObjectController.extend(App.Editable, App.FundraiserIsOwner, {
    needs: ['project'],
    actions: {
        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model');

            model.one('becameInvalid', function(record){
                model.set('errors', record.get('errors'));
                model.transitionTo('loaded.created.uncommitted');
            });

            model.one('didCreate', function(record){
                controller.transitionToRoute('fundraiser', record);
            });

            model.one('didUpdate', function(record) {
                controller.transitionToRoute('fundraiser', record);
            });

            model.save();
        }
    }
});


App.FundraiserEditController = App.FundraiserNewController.extend({
    actions: {
        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model');

            model.one('becameInvalid', function(record){
                model.set('errors', record.get('errors'));
                model.transitionTo('loaded.updated.uncommitted');
            });

            model.one('didCreate', function(record){
                controller.transitionToRoute('fundraiser', record);
            });

            model.one('didUpdate', function(record) {
                controller.transitionToRoute('fundraiser', record);
            });

            model.save();
        }
    }});


App.ProjectFundraiserAllController = Em.ArrayController.extend({
    actions: {
        showFundraiser: function(fundraiser){
            $('.modal-close').click();
            this.transitionToRoute('fundraiser', fundraiser);
        }
    }
});



App.ProjectFundraiserListController = Em.ArrayController.extend({
    needs: ['project', 'projectFundraiserAll'],

    fundraisers: function () {
        return App.Fundraiser.find({project: this.get('controllers.project.id')});
    }.property('controllers.project.id'),
    
	fundraisersLoaded: function(sender, key) {
		if (this.get(key)) {
			this.set('model', this.get('fundraisers').toArray());
		} else {
			this.set('model', null);
		}
	}.observes('fundraisers.isLoaded'),

    actions: {
        showAllFundraisers: function(project){
            // Get the controller or create one
            var controller = this.get('controllers.projectFundraiserAll');
            controller.set('model', App.Fundraiser.find({project: project.get('id'), page_size: 200}));

            // Get the view. This should be defined.
            var view = App.ProjectFundraiserAllView.create();
            view.set('controller', controller);

            var modalPaneTemplate = ['<div class="modal-wrapper"><a class="modal-close" rel="close">&times;</a>{{view view.bodyViewClass}}</div>'].join("\n");

            Bootstrap.ModalPane.popup({
                classNames: ['modal', 'large'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view,
                secondary: 'Close'
            });

        }
    }

});


App.FundraiserDonationListController = Em.ObjectController.extend({});


App.FundraiserSupporterListController = Em.ArrayController.extend({
    needs: ['fundraiser'],

    supporters: function(){
        //var project_id = this.get('controllers.fundraiser.project.id')
        var fundraiser_id = this.get('controllers.fundraiser.id')
        return App.ProjectDonation.find({fundraiser: fundraiser_id});
    }.property('controllers.fundraiser.id')


});

App.FundraiserIndexController = Em.ArrayController.extend({
    needs: ['fundraiser'],
    perPage: 5,
    page: 1,

    isOwner: function(){
        var userName = this.get('currentUser.username');
        var ownerName = this.get('controllers.fundraiser.owner.username');
        if (userName) {
            return (userName == ownerName);
        }
        return false;
    }.property('controllers.fundraiser.owner', 'controllers.fundraiser.owner.username'),

    remainingItemCount: function(){
        if (this.get('meta.total')) {
            return this.get('meta.total') - (this.get('page')  * this.get('perPage'));
        }
        return 0;
    }.property('page', 'perPage', 'meta.total'),

    canLoadMore: function(){
        var totalPages = Math.ceil(this.get('meta.total') / this.get('perPage'));
        return totalPages > this.get('page');
    }.property('perPage', 'page', 'meta.total'),

    actions: {
        showMore: function() {
            var controller = this;
            var page = this.incrementProperty('page');
            var id = this.get('controllers.fundraiser.model.id');
            App.WallPost.find({'parent_type': 'fund raiser', 'parent_id': id, page: page}).then(function(items){
                controller.get('model').pushObjects(items.toArray());
            });
        }
    }
});


App.MyFundraiserListController = Em.ArrayController.extend({});
