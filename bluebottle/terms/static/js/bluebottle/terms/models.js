App.Terms = DS.Model.extend({
    contents: DS.attr('string'),
    date: DS.attr('date'),
    version: DS.attr('string')
});


App.TermsAgreement = DS.Model.extend({
    url: 'terms/agreements',
    terms: DS.belongsTo('App.Terms'),
    user: DS.belongsTo('App.CurrentUser'),
    created: DS.attr('date')
});
