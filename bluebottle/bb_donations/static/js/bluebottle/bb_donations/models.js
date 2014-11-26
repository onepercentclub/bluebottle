/* Embedded objects */

App.Adapter.map('App.ProjectDonation', {
    user: {embedded: 'load'}
});

App.Adapter.map('App.MyFundraiserDonation', {
    user: {embedded: 'load'}
});

App.Adapter.map('App.MyProjectDonation', {
    user: {embedded: 'load'}
});


/* Models */

App.Donation = DS.Model.extend({
    amount: DS.attr('number'),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser'),
    user: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date'),
    anonymous: DS.attr('boolean', {defaultValue: false}),

    time_since: function(){
        return Globalize.format(this.get('created'), 'X');
    }.property('created')
});

App.ProjectDonation = App.Donation.extend({
    url: 'donations/project'
});

App.MyDonation = App.Donation.extend({
    url: 'donations/my',

    order: DS.belongsTo('App.MyOrder'),
    completed: DS.attr('date'),
    amount: DS.attr('number', {defaultValue: 25}),

    validAmount: function () {
        var amount = this.get('amount');
        if (amount < 5) {
            return false;
        }
        return true;

    }.property('amount')
});

App.MyFundraiserDonation = App.Donation.extend({
    url: 'donations/my/fundraisers',
});

App.MyProjectDonation = App.Donation.extend({
    url: 'donations/my/projects',
});
