pavlov.specify("Page model unit tests", function(){

    describe("Page Model", function () {
        it("is a DS.Model", function() {
            assert(App.Page).isDefined();
            assert(DS.Model.detect(App.Page)).isTrue();
        });
    });

    describe("Page Instance", function () {
        
        it("should be a new page", function () {
            build('page').then(function(page) {
                assert(page instanceof App.Page).isTrue();
                assert(page.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('page').then(function(page) {
                assert(page.url).equals('pages/en/pages');
                assert(page.get('title')).equals('Bad Prequels');
                assert(page.get('body')).equals('Episodes I, II, III. Case closed.');
            });
        });

    });

});