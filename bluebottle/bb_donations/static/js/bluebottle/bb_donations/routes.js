App.Router.map(function() {
    this.resource('myDonations', {path: '/donations'}, function(){
        this.resource('myDonationList', {path: '/history'});
    });
});


App.MyDonationsRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('myDonationList');
    }
});


App.MyDonationListRoute = Em.Route.extend({
    model: function(params) {
        return App.MyDonation.find({status: ['success', 'pending']});
    },
    setupController: function(controller, model){
        //this._super(controller, model);
        controller.set('meta', model.get('meta'));
        controller.set('model', model.toArray());
    }

});