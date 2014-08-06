/**
 *  Router Map
 */

App.Router.map(function(){
    this.resource('paymentReturn', {path: '/payments/:payment_id/:status'});
});


/**
 * Project Routes
 */

App.PaymentReturnRoute = Em.Route.extend({
    model: function(params){
        this.set('status', params.status);
        return App.Payment.find(params.payment_id);
    },
    afterModel: function(model){
        var _this = this;
        App.MyDonation.find({order: model.get('order.id')}).then(
            function(donations){
                var donation = donations.objectAt(0);
                this.transitionTo('project', donation.get('project.id'));
            },
            function(){
                throw new Em.error('Donation not found!');
            }
        );
    }
});
