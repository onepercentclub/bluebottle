pavlov.specify('Quote List View Unit Tests', function () {

  describe('App.QuoteListView Class', function () {

    it('should be an Ember.View', function () {

      assert(App.QuoteListView).isDefined();
      assert(Ember.View.detect(App.QuoteListView)).isTrue();

    });

  });

  describe('App.QuoteListView Instance', function () {

    beforeEach(function (){

      Ember.run(function() {
        view = App.QuoteListView.create();
      });

    });

    it('should have a templateName defined', function () {
 
      assert(view.templateName).isDefined();
      assert(view.templateName).equals('quote_list');

    });

  });

});