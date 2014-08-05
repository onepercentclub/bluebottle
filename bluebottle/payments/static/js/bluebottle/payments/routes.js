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
        var payment_id = params.payment_id;
        return App.Payment.find(payment_id);
    }
});
