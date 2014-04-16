App.Router.map(function(){
    this.resource('news', {path: '/news'}, function() {
        this.resource('newsItem', {path: '/:news_id'});
    });
});


/* Routes */

App.NewsRoute = Em.Route.extend({
    model: function(params) {
        return App.NewsItemPreview.find({language: App.get('language')});
    },
    setupController: function(controller, model){
        this._super(controller, model);
        this.controllerFor('application').set('latestNews', model);
    },
    events: {
        showNews: function(news_id) {
            var route = this;
            App.NewsItem.find(news_id).then(function(news) {
                route.transitionTo('newsItem', news);
                window.scrollTo(0, 0);
            });
        }
    }
});

App.NewsItemRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        var newsItem =  App.NewsItem.find(params.news_id);
        var route = this;
        newsItem.on('becameError', function() {
            route.transitionTo('error.notFound');
        });
        return newsItem;
    },
    setupController: function(controller, model) {
        this._super(controller, model);
    }
});


App.NewsIndexRoute = Em.Route.extend({
    model: function(params) {
        return App.NewsItemPreview.find({language: App.get('language')});
    },
    // Redirect to the latest news item
    setupController: function(controller, model) {
        this._super(controller, model);
        this.send('showNews', model.objectAt(0).get('id'));
    }
});

