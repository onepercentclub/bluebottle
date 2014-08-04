if (DEBUG) App.Store.registerAdapter("App.Donation", App.MockAdapter);

App.Donation = DS.Model.extend({
    amount: DS.attr('number', {defaultValue: 25}),
    projectId: DS.belongsTo('App.Project'),
    fundraiserId: DS.belongsTo('App.Fundraiser'),
    orderId: DS.belongsTo('App.Order')
});
