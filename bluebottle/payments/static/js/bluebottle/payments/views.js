App.PaymentMethodView = Em.View.extend({
    layoutName: 'payment_provider_layout',
    templateName: function(){
        return this.get('content.provider') + '/' + this.get('content.profile');
    }.property('content.provider', 'content.profile'),

    currentPaymentMethodBinding: 'controller.payment_method',

    isSelected: function() {
        return (this.get('content.uniqueId') == this.get('currentPaymentMethod.uniqueId'));
    }.property('content.uniqueId', 'currentPaymentMethod.uniqueId')


});

App.PaymentView = Em.View.extend({
    layoutName: 'payment',

    currentPaymentMethodBinding: 'controller.payment_method',

    currentPaymentMethodName: function() {
        return this.get('currentPaymentMethod.name');
    }.property('currentPaymentMethod.name'),

    currentPaymentMethodProvider: function() {
        return this.get('currentPaymentMethod.provider');
    }.property('currentPaymentMethod.provider'),

    currentPaymentMethodURL: function() {
        return 'http://www.' + this.get('currentPaymentMethod.provider') + '.com';
    }.property('currentPaymentMethod.provider'),

});

App.CreditcardView = Em.View.extend({
    cardOwner: gettext('Card Holder Name'),
    cardNumber: 'xxxx xxxx xxxx xxxx',
    expirationMonth: gettext('Month'),
    expirationYear: gettext('Year'),
    cvcCode: gettext('CVC')

});
