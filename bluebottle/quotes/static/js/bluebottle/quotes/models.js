App.Adapter.map('App.Quote', {
    user: {embedded: 'load'}
});


App.Quote = DS.Model.extend({
    url: 'quotes',

    quote: DS.attr('string'),
    user: DS.belongsTo('App.UserPreview')
});
