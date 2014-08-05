App.PaymentMethodModalController = Em.ObjectController.extend({
    methods: function(){
        var country = this.get('country');
        return App.PaymentMethod.find({country: country});
    }.property('country')

});