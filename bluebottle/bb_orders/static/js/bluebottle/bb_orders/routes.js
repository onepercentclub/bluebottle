/**
 *  Router Map
 */

App.Router.map(function(){

    // FIXME: Temporary for testing purposes
    this.resource('order', {path: '/orders/:order_id/:status'});
//    this.resource('order', {path: '/orders/:order_id'});
});


/**
 * Project Routes
 */

App.OrderRoute = Em.Route.extend({
    model: function(params){

        // FIXME: Temporary for testing purposes
        this.set('status', params.status)

        return App.MyOrder.find(params.order_id);
    },
    redirect: function(model){
        var _this = this;
        App.MyDonation.find({order: model.get('id')}).then(
            function(donations){
                // Take the first donation form the order and redirect to that project.
                var donation = donations.objectAt(0);
                _this.transitionTo('project', donation.get('project.id'));

                // FIXME: Temporary for testing purposes
                switch(_this.get('status')){
                //switch(model.get('status')){
                    case 'success':
                        _this.send('openInBox', 'donationSuccess', donation, 'modalFront');
                        break;
                    case 'pending':
                        _this.send('openInBox', 'donationSuccess', donation, 'modalFront');
                        break;
                    case 'cancelled':
                        // Create a new payment for this order
                        var payment = App.MyPayment.createRecord({order: model});
                        _this.send('openInBox', 'payment', payment, 'modalFront');
                        break;
                }
            },
            function(){
                throw new Em.error('Donation not found!');
            }
        );
    }
});
