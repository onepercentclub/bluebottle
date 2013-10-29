App.Router.map(function(){
    this.resource('news', {path: '/news'}, function() {
        this.resource('newsItem', {path: '/:news_id'});
    });
});


/* Routes */

App.NewsItemRoute = Em.Route.extend({
    model: function(params) {
        var newsItem =  App.News.find(params.news_id);
        var route = this;
        newsItem.on('becameError', function() {
            route.transitionTo('error.notFound');
        });
        return newsItem;
    }
});


App.NewsRoute = Em.Route.extend({
    model: function(params) {
        return App.NewsPreview.find({language: App.get('language')});
    }
});


App.NewsIndexRoute = Em.Route.extend({
    model: function(params) {
        return App.NewsPreview.find({language: App.get('language')});
    },
    // Redirect to the latest news item
    setupController: function(controller, model) {
        this.send('showNews', model.objectAt(0).get('id'));
    }
});

