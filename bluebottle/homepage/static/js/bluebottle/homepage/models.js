App.Adapter.map('App.HomePage', {
    projects: {embedded: 'load'},
    slides: {embedded: 'load'},
    quotes: {embedded: 'load'}
});

App.HomePage = DS.Model.extend({
    url: 'homepage',

    projects: DS.hasMany('App.ProjectPreview'),
    slides: DS.hasMany('App.Slide'),
    quotes: DS.hasMany('App.Quote'),
    project_count : DS.attr("string"),
    destination_count : DS.attr("string"),
    task_count : DS.attr("string"),
    total_hours : DS.attr("string")
});

