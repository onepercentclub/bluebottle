if (DEBUG) {
    App.Store.registerAdapter("App.Donation", App.MockAdapter);
    App.Store.registerAdapter("App.MyDonation", App.MockAdapter);
}

App.Donation = DS.Model.extend({
    amount: DS.attr('number', {defaultValue: 25}),
    project: DS.belongsTo('App.Project'),
    fundraiser: DS.belongsTo('App.Fundraiser')
});


App.MyDonation = App.Donation.extend({
    url: 'donations/my',
    order: DS.belongsTo('App.Order'),

    validAmount: function() {
        var minimumAmount = 20
        var amount = this.get('amount')
        // This regexRule will validate if the field submitted is a valid amount of money
        // a valid amount of money can be:
        // - A sequence of numbers
        // - A sequence of numbers with a comma for decimals separator
        // - A sequence of numbers with a dot for tens, hundreds, etc separator
        // - Pattern: ###.###.###,##
        // - An opposite separator pattern is also valid: ###,###,###.##
        // see http://stackoverflow.com/questions/6190312/validate-currency-amount-using-regular-expressions-in-javascript
        debugger
        var regexRule = (/(?:^\d{1,3}(?:\.?\d{3})*(?:,\d{2})?$)|(?:^\d{1,3}(?:,?\d{3})*(?:\.\d{2})?$)/)
        return ((amount.search(regexRule) == 0) && (amount > (minimumAmount)))

    }.property('amount')
});