App.PaymentMethodView = Em.View.extend({
    layoutName: 'payment_provider_layout',
    currentPaymentMethodBinding: 'controller.currentPaymentMethod',

    templateName: function(){
        return this.get('content.provider') + '/' + this.get('content.profile');
    }.property('content.provider', 'content.profile'),

    isSelected: function() {
        return (this.get('content.uniqueId') == this.get('currentPaymentMethod.uniqueId'));
    }.property('content.uniqueId', 'currentPaymentMethod.uniqueId')
});

App.CreditcardView = Em.View.extend({
    cardOwner: gettext('Card Holder Name'),
    cardNumber: 'xxxx xxxx xxxx xxxx',
    expirationMonth: gettext('Month'),
    expirationYear: gettext('Year'),
    cvcCode: gettext('CVC')
});
