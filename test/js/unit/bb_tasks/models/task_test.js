pavlov.specify("Task model unit tests", function() {

    describe("Task Model", function () {
        it("is a DS.Model", function() {
            assert(App.Task).isDefined();
            assert(DS.Model.detect(App.Task)).isTrue();
        });
    });
    
    describe("Task Instance", function () {
                
        var data = {
            title: 'Takeover Naboo',
            description: 'Title says it all!',
            end_goal: 'Description says it all!'
        }

        it("should be a new task", function () {
            build('task').then(function(task) {
                assert(task instanceof App.Task).isTrue();
                assert(task.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('task', data).then(function(task) {
                assert(task.url).equals('bb_tasks');
                assert(task.get('title')).equals(data['title']);
                assert(task.get('description')).equals(data['description']);
                assert(task.get('end_goal')).equals(data['end_goal']);
            });
        });

        it('should set the tags_list property correctly', function () {
            build('task').then(function(task) {
                assert(task.get('tags_list').length).equals(0);

                return task;
            }).then( function(task) { // Add a tag

                build('tag').then(function(tag) {

                    task.get('tags').pushObject(tag);
                    assert(task.get('tags_list')).equals(tag.get("id"));

                    return {task: task, tag1: tag};

                }).then( function(d) { // Add another tag
                    
                    build('tag').then(function(tag) {
                        d.task.get('tags').pushObject(tag);
                        var tag_list = d.tag1.get("id")+", "+tag.get("id");

                        assert(d.task.get('tags_list')).equals(tag_list);
                    });

                });
            });
        });

        it('should set status correctly', function () {
            build('task').then(function(task) {
                assert(task.get('isStatusOpen')).isTrue('status should be open');

                task.set('status', 'in progress');
                return task;
            }).then( function(task) {
                assert(task.get('isStatusInProgress')).isTrue('status should be in progress');

                task.set('status', 'closed');
                return task;
            }).then( function(task) {
                assert(task.get('isStatusClosed')).isTrue('status should be closed');

                task.set('status', 'realized');
                return task;
            }).then( function(task) {
                assert(task.get('isStatusRealized')).isTrue('status should be realized');
            });
        });

        describe('#timeNeeded', function () {

            it('should return friendly time for specific times', function () {
                build('task', {time_needed: 8}).then(function(task) {
                    assert(task.get('timeNeeded')).equals('one day', 'time needed from App.TimeNeededList');
                });
            });

            it('should return time in hours for non-specific times', function () {
                build('task', {time_needed: 2}).then(function(task) {
                    assert(task.get('timeNeeded')).equals('two hours', 'time needed in hours');
                });
            });

        });

    });

});