if (DEBUG) App.Store.registerAdapter("App.Order", App.MockAdapter); 

App.Order = DS.Model.extend({
    totalAmount: DS.attr('number'),
    // userId: DS.belongsTo('App.UserPreview'),
    donations: DS.hasMany('App.Donation')
});
