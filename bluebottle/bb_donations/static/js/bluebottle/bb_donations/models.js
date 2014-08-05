if (DEBUG) {
    App.Store.registerAdapter("App.Donation", App.MockAdapter);
    App.Store.registerAdapter("App.MyDonation", App.MockAdapter);
}

App.Donation = DS.Model.extend({
    amount: DS.attr('number', {defaultValue: 25}),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser'),
    user: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date')
});


App.MyDonation = App.Donation.extend({
    url: 'donations/my',
    order: DS.belongsTo('App.MyOrder'),

    validAmount: Em.computed.gte('amount', 5)
});