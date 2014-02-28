pavlov.specify("Quote model unit tests", function() {

    var q = 'We shouldn\'t be looking for heroes, we should be looking for good ideas.';

    describe("Quote Model", function () {

        it("is a DS.Model", function() {
            assert(App.Quote).isDefined();
            assert(DS.Model.detect(App.Quote)).isTrue();
        });
        
    });
    
    describe("Quote Instance", function () {
                
        it("should be a new quote", function () {
            build('quote').then(function(quote) {
                assert(quote instanceof App.Quote).isTrue();
                assert(quote.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('quote', {
                quote: q
            }).then(function(quote) {
                assert(quote.url).equals('quotes');
                assert(quote.get('quote')).equals(q);
                assert(quote.get('user')).isInstanceOf(App.UserPreview);
            });
        });

    });

});