/**
 * Embedded mappings
 */

App.Adapter.map('App.NewsItem', {
    author: {embedded: 'load'}
});


/**
 * Models
 */

App.NewsItem = DS.Model.extend({
    url: 'news/items',
    slug: DS.attr('string'),
    title: DS.attr('string'),
    body: DS.attr('string'),
    publicationDate: DS.attr('date'),
    author: DS.belongsTo('App.UserPreview')
});

App.NewsItemPreview = DS.Model.extend({
    url: 'news/preview-items',
    slug: DS.attr('string'),
    title: DS.attr('string'),
    publicationDate: DS.attr('date')
});

