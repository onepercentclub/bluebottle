pavlov.specify('Contact Message Route Tests', function() {

    describe('App.ContactMessageRoute Class', function () {
        it('should be an Ember.Route', function() {
            assert(App.ContactMessageRoute).isDefined();
            assert(Ember.Route.detect(App.ContactMessageRoute)).isTrue();
        });
    });

    describe('App.ContactMessageRoute Instance', function () {

        var route;

        beforeEach(function() {      
            Ember.run( function () {
                // App.injectTestHelpers(); 
                route = App.ContactMessageRoute.create();
            });

            // sinon.stub(App.CurrentUser, 'find').returns(Factory.create('user'));
        });

        afterEach(function () {
            Ember.run( function () {
                // App.removeTestHelpers();
            });

            // App.CurrentUser.find.restore();
        });

        it('should have a model property', function() {
            var model = route.model();
            assert(model).isInstanceOf(App.ContactMessage);
        });

    });
    
 });