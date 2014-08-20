App.Order = DS.Model.extend({
    status: DS.attr('string'),
    user: DS.belongsTo('App.UserPreview'),
    country: DS.belongsTo('App.Country'),
    totalAmount: DS.attr('number'),
    donations: DS.hasMany('App.Donation'),
    created: DS.attr('date')
});

App.MyOrder = App.Order.extend({
    url: 'orders/my'
});
