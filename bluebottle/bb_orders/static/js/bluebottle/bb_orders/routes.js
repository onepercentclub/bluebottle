/**
 *  Router Map
 */

App.Router.map(function(){
    // FIXME: Temporary for testing purposes
    this.resource('order', {path: '/orders/:order_id/:status'});
    // this.resource('order', {path: '/orders/:order_id'});
});

/**
 * Project Routes
 */
App.OrderRoute = Em.Route.extend({
    model: function(params) {
        // FIXME: Temporary for testing purposes
        this.set('status', params.status);

        return App.MyOrder.find(params.order_id);
    },

    redirect: function(model) {
        var _this = this,
            status = _this.get('status');

        App.MyDonation.find({order: model.get('id')}).then(
            function(donations){
                // Take the first donation form the order and redirect to that project.
                var donation = donations.objectAt(0);

                // FIXME: For testing purposes we need to reload the project here.
                //        We also need to handle the donation on a fundraiser.
                donation.get('project').reload().then( function () {
                    _this.transitionTo('project', donation.get('project.id')).promise.then(function () {
                        // FIXME: Temporary for testing purposes
                        switch (status) {
                            case 'success':
                                // The model for the donation success modal is a 
                                // wallpost with the parent details set based on 
                                // the type of donation.
                                var donationType = donation.get('project') ? 'project' : 'fundraiser';

                                var post = App.TextWallPost.createRecord({
                                    parent_type: donationType,
                                    parent_id: donation.get(donationType).get('id')
                                });

                                _this.send('openInDynamic', 'paymentSuccess', post, 'modalFront');
                                break;

                            case 'pending':
                                _this.send('openInDynamic', 'paymentPending', donation, 'modalFront');
                                break;

                            case 'cancelled':
                                // Create a new payment for this order
                                var payment = App.MyPayment.createRecord({order: model});

                                _this.send('openInDynamic', 'payment', payment, 'modalFront');
                                break;
                        }
                    });
                });
            },
            function(){
                throw new Em.error('Donation not found!');
            }
        );
    }
});
