pavlov.specify('News Route Tests', function() {

    describe('App.NewsRoute Class', function () {
        it('should be an Ember.Route', function() {
            assert(App.NewsRoute).isDefined();
            assert(Ember.Route.detect(App.NewsRoute)).isTrue();
        });
    });

    describe('App.NewsRoute Instance', function () {

        var route;

        before(function() {      
            Ember.run( function () {
                App.injectTestHelpers();

                route = App.NewsRoute.create();
            });
        });

        after(function () {
            Ember.run( function () {
                App.removeTestHelpers();

                App.Task.FIXTURES = [];
            });
        });

        it('should have a model property', function() {
            var model = route.model();
            assert(model).isInstanceOf(DS.AdapterPopulatedRecordArray);
        });

    });
    
 });