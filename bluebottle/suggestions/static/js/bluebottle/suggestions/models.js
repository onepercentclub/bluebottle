
App.Suggestion = DS.Model.extend({
    url: 'suggestions',

    title: DS.attr('string'),
    pitch: DS.attr('string'),
    deadline: DS.attr('date'),
    theme: DS.belongsTo('App.Theme'),
    destination: DS.attr('string'),

    org_contactname : DS.attr('string'),
    org_name : DS.attr('string'),
    org_email : DS.attr('string'),
    org_phone : DS.attr('string'),
    org_website : DS.attr('string'),

    status : DS.attr('string'),
    project: DS.belongsTo("App.Project"),

    token: DS.attr('string'),

    isUnconfirmed: Em.computed.equal('status', 'unconfirmed'),
    isDraft: Em.computed.equal('status', 'draft'),
    isAccepted: Em.computed.equal('status', 'accepted'),
    isRejected: Em.computed.equal('status', 'rejected'),
    isExpired: Em.computed.equal('status', 'expired'),
    isInProgress: Em.computed.equal('status', 'in_progress'),
    isSubmitted: Em.computed.equal('status', 'submitted')

});