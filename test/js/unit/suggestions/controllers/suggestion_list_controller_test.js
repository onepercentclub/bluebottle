pavlov.specify("Suggestion List Test", function() {

    describe("App.SuggestionListController", function () {

        var suggestionListController, suggestions;

        beforeEach(function () {
            // App.reset();
            Ember.run(function () {
                suggestionListController = App.SuggestionListController.create();
                suggestions = Em.ArrayProxy.create({content: Ember.A([])});

            });
        });

        afterEach(function () {
          Ember.run(function () {
            suggestionListController.destroy();
            suggestions.destroy();
          });
        });

        it("should have a computed property totalSugggestions is 0", function () {
            assert(suggestionListController.get('totalSuggestions')).equals(0); 
        });

        it("should have a computed property hasSuggestions which is false", function () {
            assert(suggestionListController.get('hasSuggestions')).isFalse(); 
        });

        it("should return the correct number of suggestions", function () {
            var suggestions = Em.ArrayProxy.create({content: Ember.A([])});

            build('suggestion').then(function(suggestionA) {
                suggestions.pushObject(suggestionA);
                suggestionListController.set('model', suggestions); 
                assert(suggestionListController.get('totalSuggestions')).equals(1);     

            }).then(function() {
                build('suggestion').then(function(suggestionB) {
                    suggestions.pushObject(suggestionB);
                    suggestionListController.set('model', suggestions); 
                    assert(suggestionListController.get('totalSuggestions')).equals(2); 
                }).then(function() {
                    suggestions.popObject();
                    suggestionListController.set('model', suggestions); 
                    assert(suggestionListController.get('totalSuggestions')).equals(1);    
                });
            });
        });   

        it("should set hasSuggestions correctly", function () {

            suggestionListController.set('model', suggestions); 
            assert(suggestionListController.get('totalSuggestions')).equals(0);     

            assert(suggestionListController.get('hasSuggestions')).isFalse();     

            build('suggestion').then(function(suggestion) {
                suggestions.pushObject(suggestion);
                suggestionListController.set('model', suggestions); 
                assert(suggestionListController.get('totalSuggestions')).equals(1);     
                assert(suggestionListController.get('hasSuggestions')).isTrue(); 
            });
        });   

    });

});