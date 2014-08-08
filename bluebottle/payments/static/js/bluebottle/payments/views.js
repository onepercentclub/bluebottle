App.PaymentMethodView = Em.View.extend({
    layoutName: 'payment_provider_layout',
    templateName: function(){
        return this.get('content.provider') + '/' + this.get('content.profile');
    }.property('content.provider', 'content.profile'),

    currentPaymentMethodBinding: 'controller.currentPaymentMethod',

    isSelected: function() {
        return (this.get('content.uniqueId') == this.get('currentPaymentMethod.uniqueId'));
    }.property('content.uniqueId', 'currentPaymentMethod.uniqueId')
});