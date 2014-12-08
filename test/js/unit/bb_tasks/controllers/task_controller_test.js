pavlov.specify("Task Controller Test", function() {

    describe("App.TaskController", function () {

      var taskController, taskModel;

      beforeEach(function () {
        // App.reset();
        var taskMember = create('taskMember');
        var taskController = App.TaskController.create();
        taskController.set('model', taskMember);

        // Ember.run(function () {
        //   , function () {
        //     debugger
        //     var container = App.__container__;
        //     taskController = container.lookup('controller:task');
        //     taskController.set('model', taskMember.task);            
        //   });

        // });
      });

      afterEach(function () {
        Ember.run(function () {
          taskMember.destroy();
          taskController.destroy();
        });
      });

      // it("should have a computed property isMember", function () {
      //   Ember.run(function () {
      //     // isMember compares the current users user_id to the book owner's user id (hence the need to hit the users controller from the book) - note this is a made up example
      //     expect(taskController.get('isMember')).toBeTruthy();
      //   });
      // });

    });

});
