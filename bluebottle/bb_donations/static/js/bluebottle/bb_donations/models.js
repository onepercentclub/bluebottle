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
<<<<<<< HEAD
    amount: DS.attr('number', {defaultValue: 25 + ',-'}),
    project: DS.belongsTo('App.Project'),
=======
    amount: DS.attr('number'),
    project: DS.belongsTo('App.ProjectPreview'),
>>>>>>> feature/fund-loving-criminals
    fundraiser: DS.belongsTo('App.Fundraiser'),
    user: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date')
});

App.ProjectDonation = DS.Model.extend({
    url: 'donations/project',
    amount: DS.attr('number'),
    created: DS.attr('date'),
    user: DS.belongsTo('App.UserPreview')
});

App.MyDonation = App.Donation.extend({
    url: 'donations/my',
    order: DS.belongsTo('App.MyOrder'),
    amount: DS.attr('number', {defaultValue: 25}),
    validAmount: Em.computed.gte('amount', 5)
});
