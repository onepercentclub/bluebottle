/**
 *  Router Map
 */

App.Router.map(function() {
    // The empty function is there for the fundraiserIndex route to be called.
    this.resource('fundraiser', {path: '/fundraisers/:fundraiser_id'}, function(){});

    this.resource('fundraiserEdit', {path: '/fundraisers/:fundraiser_id/edit'});

    this.resource('fundraiserNew', {path: '/projects/:project_id/new-fundraiser'});

    this.resource('myFundraiserList', {path: '/my/fundraisers'});

    this.resource('fundraiserDonationList', {path: '/fundraisers/:fundraiser_id/donations'});
});


/**
 * Fundraiser Routes
 */
App.FundraiserRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        // Crap hack because Ember somehow doesn't strip queryparams.
        // FIXME: Find out this -should- work.
        var fundraiser_id = params.fundraiser_id.split('?')[0];
        return App.Fundraiser.find(fundraiser_id);
    }
});


App.FundraiserIndexRoute = Em.Route.extend({
    // This way the ArrayController won't hold an immutable array thus it can be extended with more wall-posts.
    setupController: function(controller, model) {
        var parent_id = this.modelFor('fundraiser').get('id');
        // Only reload this if switched to another fundraiser.
        if (controller.get('parent_id') != parent_id){
            controller.set('page', 1);
            controller.set('parent_id', parent_id);
            App.WallPost.find({'parent_type': 'fund raiser', 'parent_id': parent_id}).then(function(items){
                controller.set('meta', items.get('meta'));
                controller.set('model', items.toArray());
            });
        }
    }
});


App.FundraiserNewRoute = Em.Route.extend(App.ScrollToTop, {
    googleConversion: {
        label: 'P4TmCIKA7AsQ7o7O1gM'
    },

    model: function(params) {
        // Using project preview to have less data attached (TODO: Verify!)
        var store = this.get('store');

        var projectPreview = App.ProjectPreview.find(params.project_id);

        return store.createRecord(App.Fundraiser, {project: projectPreview});
    }
});

App.FundraiserEditRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.Fundraiser.find(params.fundraiser_id);
    }
});


App.FundraiserDonationListRoute = Em.Route.extend({
    model: function(params) {
        // Crap hack because Ember somehow doesn't strip queryparams.
        // FIXME: Find out this -should- work.
        var fundraiser_id = params.fundraiser_id.split('?')[0];
        return App.Fundraiser.find(fundraiser_id);
    },

    setupController: function(controller, fundraiser) {
        this._super(controller, fundraiser);

        controller.set('fundRaiseDonations', App.MyFundraiserDonation.find({fundraiser: fundraiser.id}));
    }
});


App.MyFundraiserListRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.CurrentUser.find('current').then(function(user) {
            var user_id = user.get('id_for_ember');
            return App.Fundraiser.find({owner: user_id});
        });
    },
    setupController: function(controller, model) {
        this._super(controller, model);
    }
});
//
// TOOD: Unused at this time.
//App.MyFundraiserRoute = Em.Route.extend({
//    model: function(params) {
//        return App.Fundraiser.find(params.my_fundraiser_id);
//    }
//});
