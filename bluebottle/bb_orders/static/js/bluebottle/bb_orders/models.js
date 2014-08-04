if (DEBUG) {
    App.Store.registerAdapter("App.Order", App.MockAdapter); 
    App.Store.registerAdapter("App.MyOrder", App.MockAdapter); 
}

App.Order = DS.Model.extend({
    status: DS.attr('string'),
    userId: DS.belongsTo('App.UserPreview'),
    totalAmount: DS.attr('number'),
    donations: DS.hasMany('App.Donation')
});

App.MyOrder = App.Order.extend({
    url: 'orders/my',
});
