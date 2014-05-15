pavlov.specify("Organization model unit tests", function() {

    data = {
      name: 'Galactic Podracing Mechanics Union',
      description: 'The Galactic Podracing Mechanics Union was an organization active during the final decades of the Galactic Republic',
      website: 'www.gpmu.org',
      facebook: 'facebook.com/gpmu',
      twitter: '@gpmu',
      legalStatus: 'good'
    }

    describe("Organization Model", function () {
        it("is a DS.Model", function() {
            assert(App.Organization).isDefined();
            assert(DS.Model.detect(App.Organization)).isTrue();
        });
    });
    
    describe("Project Instance", function () {
        
        it("should be a new org", function () {
            build('organization', data).then(function(org) {
                assert(org instanceof App.Organization).isTrue();
                assert(org.get('isNew')).isTrue();
            });
        });

        it("should have some properties", function () {
            build('organization', data).then(function(org) {
                assert(org.url).equals('bb_organizations');
                assert(org.get('name')).equals(data['name']);
                assert(org.get('description')).equals(data['description']);
                assert(org.get('legalStatus')).equals(data['legalStatus']);
            });
        });

        it('should format external urls correctly', function () {
            build('organization', data).then(function(org) {
                assert(org.get('websiteUrl')).equals('http://www.gpmu.org');
                assert(org.get('facebookUrl')).equals('http://facebook.com/gpmu');
                assert(org.get('twitterUrl')).equals('http://twitter.com/gpmu');
            });
        });

    });

});