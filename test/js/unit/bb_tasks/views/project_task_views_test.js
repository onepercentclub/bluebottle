pavlov.specify('Project Task Edit View Tests', function() {

    describe('App.TaskEditView Class', function () {
        it('should be an Ember.View', function() {
            assert(App.TaskEditView).isDefined();
            assert(Ember.View.detect(App.TaskEditView)).isTrue();
        });
    });

    describe('App.TaskEditView Instance', function () {

        var view;

        beforeEach(function () {
            Ember.run( function () {
                view = App.TaskEditView.create();
            });
        });

        it('should respond to submit action', function() {
            assert(view.submit).isFunction();
        });

        it('should call updateTask when submit action triggered', function () {
            // stub some stuff
            var event = { preventDefault: function () {} };
            var controller = { updateTask: function () {} };
            var spy = sinon.spy(controller, 'updateTask');

            // call submit
            view.set('controller', controller);
            view.submit(event);

            assert(spy.calledOnce).isTrue();
        });
    });
 });

pavlov.specify('Project Task New View Tests', function() {

    describe('App.TaskNewView', function () {
        it('should be an Ember.View', function() {
            assert(App.TaskNewView).isDefined();
            assert(Ember.View.detect(App.TaskNewView)).isTrue();
        });
    });

    describe('App.TaskNewView Instance', function () {

        var view;

        beforeEach(function () {
            Ember.run( function () {
                view = App.TaskNewView.create();
            });
        });

        it('should respond to submit action', function() {
            assert(view.submit).isFunction();
        });

        it('should call createTask when submit action triggered', function () {
            // stub some stuff
            var event = { preventDefault: function () {} };
            var controller = { createTask: function () {} };
            var spy = sinon.spy(controller, 'createTask');

            // call submit
            view.set('controller', controller);
            view.submit(event);

            assert(spy.calledOnce).isTrue();
        });
    });
 });