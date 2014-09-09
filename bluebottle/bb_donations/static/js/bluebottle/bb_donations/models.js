/* Embedded objects */

App.Adapter.map('App.ProjectDonation', {
    user: {embedded: 'load'}
});


/* Models */

App.Donation = DS.Model.extend({
    amount: DS.attr('number'),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.FundRaiser'),
    user: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date'),
    anonymous: DS.attr('boolean', {defaultValue: false})
});

App.ProjectDonation = DS.Model.extend({
    url: 'donations/project',

    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.FundRaiser'),

    amount: DS.attr('number'),
    created: DS.attr('date'),
    user: DS.belongsTo('App.UserPreview')
});

App.MyDonation = App.Donation.extend({
    url: 'donations/my',

    order: DS.belongsTo('App.MyOrder'),
    amount: DS.attr('number'),

    defaultAmount: 25,

    validAmount: function () {
        var amount = this.get('amount');
        if (!amount) {
            //if no amount set the default amount
            this.set('amount', this.get('defaultAmount'));
        } else if (amount < 5) {
            return false;
        }
        return true;

    }.property('amount')
});
