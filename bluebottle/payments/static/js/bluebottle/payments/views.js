App.PaymentMethodView = Em.View.extend({
    layoutName: 'payment_provider_layout',
    templateNameBinding: 'content.profile',
    currentPaymentMethodBinding: 'controller.currentPaymentMethod',

    isSelected: function() {
        return (this.get('content.uniqueId') == this.get('currentPaymentMethod.uniqueId'));
    }.property('content.uniqueId', 'currentPaymentMethod.uniqueId')
});