App.Store.registerAdapter("App.Payment", App.MockAdapter); 
App.Store.registerAdapter("App.PaymentMethod", App.MockAdapter); 

App.Payment = DS.Model.extend({
    amount: DS.attr('number'),
    paymentMethodId: DS.belongsTo('App.PaymentMethod'),
    orderId: DS.belongsTo('App.Order'),
    status: DS.attr('string')
});

App.PaymentMethod = DS.Model.extend({
    amount: DS.attr('number'),
    providerId: DS.attr('number'),
    paymentType: DS.attr('string'),
    paymentProcess: DS.attr('string')
});
