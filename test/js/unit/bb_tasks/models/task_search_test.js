pavlov.specify("Task Search model unit tests", function() {

    describe("Task Search Model", function () {
        it("is a DS.Model", function() {
            assert(App.TaskSearch).isDefined();
            assert(DS.Model.detect(App.TaskSearch)).isTrue();
        });
    });
    
    describe("Task Search Instance", function () {
                
        it("should be a new task search", function () {
            build('taskSearch').then(function(taskSearch) {
                assert(taskSearch instanceof App.TaskSearch).isTrue();
                assert(taskSearch.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('taskSearch').then(function(taskSearch) {
                assert(taskSearch.get('text')).equals('star');
                assert(taskSearch.get('skill')).equals('Engineer');
                assert(taskSearch.get('ordering')).equals('newest');
                assert(taskSearch.get('status')).equals('open');
                assert(taskSearch.get('page')).equals(1);
            });
        });

    });

});