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

App.OrderPaymentView = Em.View.extend({
    templateName: 'order_payment',

    matchCreditcardChange: function(e) {
        var x = e.target.className,
            prntElm = $('.card-item .icon-card'),
            elmValue = '.icon-card' + '.' + e.target.value;

        if (x.match("creditcard-select")) {
            prntElm.removeClass('is-selected');
            prntElm.addClass('is-unselected');
            $(elmValue).addClass('is-selected');
        }
    }.on('change'),

    matchCreditcardClick: function(e){
        var x = e.target.className,
            elm = $(e.target),
            prntElm = $('.card-item .icon-card'),
            cardName;

        if (x.match("icon-card")) {
            prntElm.removeClass('is-selected');
            prntElm.addClass('is-unselected');
            elm.addClass('is-selected');
            cardName = x.split(" ");

            $(".creditcard-select option[value=" + cardName[1] +"]").attr('selected','selected');
            $('.payment-btn').removeClass('is-inactive');
        }
    }.on('click')
});

