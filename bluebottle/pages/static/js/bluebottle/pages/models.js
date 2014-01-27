/* Models */


App.Page = DS.Model.extend({
    url: 'pages/en/pages', // TODO: Temporary fix. Solve it to handle internationalization.
    title: DS.attr('string'),
    body: DS.attr('string'),
    full_page: DS.attr('boolean')
});


App.PartnerOrganization = DS.Model.extend({
    url: 'partners',
    name: DS.attr('string'),
    projects: DS.hasMany('App.ProjectPreview'),
    description: DS.attr('string'),
    image: DS.attr('image')
});
