/*
 * Router mapping
 */

App.Router.map(function() {
    this.resource('page', {path: '/pages/:page_id'});
});


/* Static Pages */

App.PageRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        var model = App.Page.find(params.page_id);
        var route = this;
        model.on('becameError', function() {
            route.transitionTo('error.notFound');
        });
        return model;
    }
});
