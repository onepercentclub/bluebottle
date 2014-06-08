/*
 * Router mapping
 */

App.Router.map(function() {
    this.resource('page', {path: '/pages/:page_id'});
});


/* Static Pages */

App.PageRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.Page.find(params.page_id);
    },
    actions: {
        error: function(error, transition) {
            // TODO: maybe we shouldn't transition. Instead we keep the 
            //       same route and render the error template. This would
            //       allow the user to check the url and correct easily.
            this.transitionTo('error.notFound');
        }
    }
});
