
App.Suggestion = DS.Model.extend({
    url: 'suggestions',
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    deadline: DS.attr('date'),
    theme: DS.attr('string'),
    destination: DS.attr('string'),

    org_name = DS.attr('string'),
    org_contactname = DS.attr('string'),
    org_email = DS.attr('string'),
    org_phone = DS.attr('string'),
    org_website = DS.attr('string'),

    status = DS.attr('string'),
    project: DS.belongsTo("App.Project")
});