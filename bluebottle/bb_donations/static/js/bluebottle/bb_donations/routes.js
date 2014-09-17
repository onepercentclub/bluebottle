App.Router.map(function() {
    this.resource('myDonationList', {path: '/my/donations'});
});

App.MyDonationListRoute = Em.Route.extend({
    model: function(params) {
        return App.MyDonation.find({status: 'success'});
    }
});