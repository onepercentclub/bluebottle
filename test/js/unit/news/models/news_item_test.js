pavlov.specify("News Item model unit tests", function() {

    var data = {
        slug: 'storm-troopers-strike',
        title: 'Storm Troopers Strike Again',
        body: 'Storm Troopers on strike for the second time this year. Darth Vadar said to be unhappy.',
    }

    describe("News Item Model", function () {
        it("is a DS.Model", function() {
            assert(App.NewsItem).isDefined();
            assert(DS.Model.detect(App.NewsItem)).isTrue();
        });
    });
    
    describe("News Item Instance", function () {

        it("should be a new task file", function () {
            build('newsItem').then(function(newsItem) {
                assert(newsItem instanceof App.NewsItem).isTrue();
                assert(newsItem.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('newsItem', data).then(function(newsItem) {
                assert(newsItem.url).equals('news/items');
                assert(newsItem.get('title')).equals(data['title']);
                assert(newsItem.get('slug')).equals(data['slug']);
            });
        });

    });

});