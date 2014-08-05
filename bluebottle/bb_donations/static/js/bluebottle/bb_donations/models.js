if (DEBUG) App.Store.registerAdapter("App.Donation", App.MockAdapter);

App.Donation = DS.Model.extend({
    amount: DS.attr('number', {defaultValue: 25}),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser')
});


App.MyDonation = App.Donation.extend({
    url: 'donations/my',
    order: DS.belongsTo('App.Order')
});