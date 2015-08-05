pavlov.specify("Suggestion Test", function() {

    describe("App.SuggestionController", function () {

        var suggestionController, suggestion, theme;

        beforeEach(function () {
            Ember.run(function () {
                suggestionController = App.SuggestionController.create();
                create('suggestion').then(function(loadedSuggestion) {
                    suggestion = loadedSuggestion
                    suggestionController.set('model', loadedSuggestion)
                });

            });
        });

        afterEach(function () {
          Ember.run(function () {
            suggestionController.destroy();
          });
        });

        it("should have a property 'errors' that is null", function () {
            assert(suggestionController.get('errors')).isNull("errors is null");
  
        });

        it("should create an organization without errors", function() {
            var beforeLength,
                afterLength,
                org;
            
            Ember.run(function () {
                beforeLength = App.MyOrganization.find().get('length');
                suggestionController.createOrganization();
            });

            afterLength = App.MyOrganization.find().get('length');

            assert(beforeLength).isEqualTo(afterLength-1);

            org = App.MyOrganization.find().get('firstObject');

            assert(org.get('title'), suggestion.get('title'));
            assert(org.get('destination'), suggestion.get('title'));
            assert(org.get('name'), suggestion.get('org_name'));
            assert(org.get('phone'), suggestion.get('org_phone'));
            assert(org.get('website'), suggestion.get('org_website'));
            assert(org.get('email'), suggestion.get('org_email'));
        });

        it("should create a project without errors", function() {
            var beforeLength,
                afterLength,
                org,
                project;
            
            Ember.run(function () {
                beforeLength = App.MyProject.find().get('length');
                suggestionController.createProject();
            });

            afterLength = App.MyProject.find().get('length');

            assert(beforeLength).isEqualTo(afterLength-1);

            project = App.MyProject.find().get('firstObject')

            assert(project.get('title'), suggestion.get('title'));
            assert(project.get('pitch'), suggestion.get('pitch'));
            assert(project.get('deadline'), suggestion.get('deadline'));
            assert(project.get('theme'), suggestion.get('theme'));

        });

        it("should update a suggestion correctly", function() {
            assert(suggestion.get('status')).isEqualTo('unconfirmed');

            Ember.run(function(){
                suggestion.set('project', null);
            });
            assert(suggestion.get('project')).isNull("has no project");

            Ember.run(function () {
                suggestionController.createProject();
            });

            project = App.MyProject.find().get('firstObject')

            Ember.run(function () {
                suggestionController.updateSuggestion(project);
            });

            assert(suggestion.get('status')).isEqualTo('in_progress');
            assert(suggestion.get('project')).isEqualTo(project);
        });
    });

});