if (DEBUG) App.Store.registerAdapter("App.Payment", App.MockAdapter); 

App.Payment = DS.Model.extend({
    totalAmount: DS.attr('number'),
    // userId: DS.belongsTo('App.UserPreview'),
    donations: DS.hasMany('App.Donation')
});
