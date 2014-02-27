pavlov.specify("News Item Preview model unit tests", function() {

    var data = {
        slug: 'darth-vadar-unhappy',
        title: 'Darth Vadar unhappy with Storm Troopers',
        publicationDate: new Date(2014,01,01)
    }

    describe("News Item Preview Model", function () {
        it("is a DS.Model", function() {
            assert(App.NewsItemPreview).isDefined();
            assert(DS.Model.detect(App.NewsItemPreview)).isTrue();
        });
    });
    
    describe("News Item Preview Instance", function () {
                
        it("should be a new task file", function () {
            build('newsItemPreview').then(function(newsItemPreview) {
                assert(newsItemPreview instanceof App.NewsItemPreview).isTrue();
                assert(newsItemPreview.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('newsItemPreview', data).then(function(newsItemPreview) {
                assert(newsItemPreview.url).equals('news/preview-items');
                assert(newsItemPreview.get('title')).equals(data['title']);
                assert(newsItemPreview.get('slug')).equals(data['slug']);
            });
        });

    });

});