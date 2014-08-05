App.PaymentMethodModalController = Em.ArrayController.extend({
    needs: ['donationModal'],
    order: function(){
        return this.get('controllers.donationModal.order');
    }.property('controllers.donationModal.model')

});