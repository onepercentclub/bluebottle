pavlov.specify("Suggestion model unit tests", function() {

    describe("Suggestion Model", function () {
        it("is a DS.Model", function() {
            assert(App.Suggestion).isDefined();
            assert(DS.Model.detect(App.Suggestion)).isTrue();
        });
    });
    
    describe("Suggestion Instance", function () {
                
        var data = {
            title: 'Suggestion: Kill the rebels',
            pitch: 'Lets wipe them all out',
            deadline: new Date(2016, 12, 1),
            //theme: 'Party of destruction',
            destination: 'Hell',
            org_name: 'Rebel Alliance',
            org_contactname: "Leia Organa",
            org_email: "leia69@hotmail.com",
            org_phone: '555-1254',
            org_website: 'www.rebelalliance.com'
        };

        it('should be a new suggestion', function() {
            build('suggestion').then(function(suggestion) {
                assert(suggestion instanceof App.Suggestion).isTrue();
                assert(suggestion.get('isUnconfirmed')).isTrue()
            });
        });

        it("shoud have some properties", function() {
            build('suggestion', data).then(function(suggestion) {
                assert(suggestion.get('title')).equals(data['title']);
                assert(suggestion.get('pitch')).equals(data['pitch']);
                assert(suggestion.get('deadline')).equals(data['deadline']);
                //assert(suggestion.get('theme')).equals(data['theme']);
                assert(suggestion.get('destination')).equals(data['destination']);
                assert(suggestion.get('org_name')).equals(data['org_name']);
                assert(suggestion.get('org_contactname')).equals(data['org_contactname']);
                assert(suggestion.get('org_email')).equals(data['org_email']);
                assert(suggestion.get('org_phone')).equals(data['org_phone']);
                assert(suggestion.get('org_website')).equals(data['org_website']);
            });
        })

        it('should set status correctly', function () {
            build('suggestion').then(function(suggestion) {
                assert(suggestion.get('isUnconfirmed')).isTrue('status should be unconfirmed');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'draft');
                assert(suggestion.get('isDraft')).isTrue('status should be draft');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'accepted');
                assert(suggestion.get('isAccepted')).isTrue('status should be accepted');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'rejected');
                assert(suggestion.get('isRejected')).isTrue('status should be rejected');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'expired');
                assert(suggestion.get('isExpired')).isTrue('status should be expired');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'in_progress');
                assert(suggestion.get('isInProgress')).isTrue('status should be in_progress');
                return suggestion;
            }).then( function(suggestion) {
                suggestion.set('status', 'submitted');
                assert(suggestion.get('isSubmitted')).isTrue('status should be submitted');
                return suggestion;
            });
        });

    });

});