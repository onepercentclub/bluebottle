/* Models */


App.Page = DS.Model.extend({
    url: 'pages/en/pages', // TODO: Temporary fix. Solve it to handle internationalization.
    title: DS.attr('string'),
    body: DS.attr('string'),
    full_page: DS.attr('boolean')
});

