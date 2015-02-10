pavlov.specify('Suggestion List View Unit Tests', function () {

    describe('App.SuggestionListView Class', function () {

        var suggestionListController, suggestionListView, suggestions;

        beforeEach(function () {
            // App.reset();
            Ember.run(function () {
                suggestionListController = App.SuggestionListController.create();
                suggestions = Em.ArrayProxy.create({content: Ember.A([])});
                suggestionListView = Em.View.create({
                    container: App.__container__,
                    templateName: 'suggestion_list',
                    controller: suggestionListController
              })

            });
        });

        it('should be an Ember.View', function () {
            assert(suggestionListView).isInstanceOf(Em.View, 'Its an Ember View');
        });

        it('should correctly render the list of suggestions', function() {
            assert(find('ul').length, 0, 'There is no list');

            build('suggestion').then(function(suggestionA) {
                suggestions.pushObject(suggestionA);
                suggestionListController.set('model', suggestions); 
                assert(suggestionListController.get('totalSuggestions')).equals(1);
                assert(find('ul').length, 1, 'There is a list');
                assert(find('li').length, 1, 'There is one suggestion');
                assert(find('li').html(), suggestionA.get('title'), 'Suggestion A title is correct');
                return suggestionA;

            }).then(function(suggestionA) {
                build('suggestion').then(function(suggestionB) {
                    suggestions.pushObject(suggestionB);
                    suggestionListController.set('model', suggestions); 
                    assert(suggestionListController.get('totalSuggestions')).equals(2); 
                    assert(find('li').length, 2, 'There are two suggestions');
                    assert(find('li:first-of-type').html(), suggestionA.get('title'), 'Suggestion A title is correct');
                    assert(find('li:last-of-type').html(), suggestionB.get('title'), 'Suggestion B title is correct');
                }); 
            });
        });


        });

});