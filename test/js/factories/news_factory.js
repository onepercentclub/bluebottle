Factory.define('newsItem', {
    slug: function(app) { 'news-item-slug-' + Math.floor((Math.random()*1000)+1) },
    title: 'News Item Title',
    body: 'News Item Body',
    publicationDate: function(app) { return new Date(); },
    author: function() { return attr('userPreview'); },
});

Factory.define('newsItemPreview', {
    slug: function(app) { return 'news-item-preview-slug-' + Math.floor((Math.random()*1000)+1) },
    title: 'News Item Preview Title',
    publicationDate: function(app) { return new Date(); }
});