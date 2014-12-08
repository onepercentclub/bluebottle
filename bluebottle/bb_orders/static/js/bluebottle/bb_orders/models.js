App.Adapter.map('App.MyOrder', {
    donations: {embedded: 'load'}
});

App.Order = DS.Model.extend({
    status: DS.attr('string'),
    country: DS.belongsTo('App.Country'),
    totalAmount: DS.attr('number'),
    donations: DS.hasMany('App.Donation'),
    created: DS.attr('date')
});

App.MyOrder = App.Order.extend({
    url: 'orders/my',
    donations: DS.hasMany('App.MyDonation'),
    user: DS.belongsTo('App.UserPreview')
});
