if (DEBUG) {
    App.Store.registerAdapter("App.Donation", App.MockAdapter);
    App.Store.registerAdapter("App.ProjectDonation", App.MockAdapter);
    App.Store.registerAdapter("App.MyDonation", App.MockAdapter);

    App.MockAdapter.map('App.ProjectDonation', {
        user: {embedded: 'load'}
    });

    App.MockAdapter.map('App.MyDonation', {
        project: {embedded: 'load'}
    });


}

/* Embedded objects */

App.Adapter.map('App.ProjectDonation', {
    user: {embedded: 'load'}
});

App.Adapter.map('App.MyDonation', {
    project: {embedded: 'load'}
});





/* Models */

App.Donation = DS.Model.extend({
    amount: DS.attr('number'),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser')
});

App.ProjectDonation = DS.Model.extend({
    url: 'donations/project',
    amount: DS.attr('number'),
    created: DS.attr('date'),
    user: DS.belongsTo('App.UserPreview')
});

App.MyDonation = App.Donation.extend({
    url: 'donations/my',
    amount: DS.attr('number', {defaultValue: 25}),
    order: DS.belongsTo('App.Order')
});