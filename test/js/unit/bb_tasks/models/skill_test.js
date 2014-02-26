pavlov.specify("Skill model unit tests", function() {

    describe("Skill Model", function () {
        it("is a DS.Model", function() {
            assert(App.Skill).isDefined();
            assert(DS.Model.detect(App.Skill)).isTrue();
        });
    });
    
    describe("Skill Instance", function () {

        before(function() {      
            Ember.run( function () {
                App.injectTestHelpers();
            });
        });

        after(function () {
            Ember.run( function () {
                App.removeTestHelpers();
            });
        });

        it("should be a new skill", function () {
            build('skill').then(function(skill) {
                assert(skill instanceof App.Skill).isTrue();
                assert(skill.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('skill').then(function(skill) {
                assert(skill.url).equals('bb_tasks/skills');
                assert(skill.get('name')).equals('Mind Control');
            });
        });

    });

});