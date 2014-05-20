pavlov.specify("Task File model unit tests", function() {

    describe("Task File Model", function () {
        it("is a DS.Model", function() {
            assert(App.TaskFile).isDefined();
            assert(DS.Model.detect(App.TaskFile)).isTrue();
        });
    });
    
    describe("Task File Instance", function () {
                
        it("should be a new task file", function () {
            build('taskFile').then(function(taskFile) {
                assert(taskFile instanceof App.TaskFile).isTrue();
                assert(taskFile.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('taskFile').then(function(taskFile) {
                assert(taskFile.url).equals('bb_tasks/files');
                assert(taskFile.get('title')).equals('Death Star Blueprints');
                assert(taskFile.get('file')).equals('deathstar.pdf');
                assert(taskFile.get('author') instanceof App.User).isTrue();
                assert(taskFile.get('task') instanceof App.Task).isTrue();
            });
        });

    });

});