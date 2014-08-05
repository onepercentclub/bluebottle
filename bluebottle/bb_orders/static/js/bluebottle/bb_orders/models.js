App.Order = DS.Model.extend({
    status: DS.attr('string'),
    user: DS.belongsTo('App.UserPreview'),
    country: DS.belongsTo('App.Country'),
    total: DS.attr('number'),
    donations: DS.hasMany('App.Donation')
});

App.MyOrder = App.Order.extend({
    url: 'orders/my'
});
