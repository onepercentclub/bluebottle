App.Adapter.map('App.MyOrganization', {
    documents: {embedded: 'load'}
});

App.Adapter.map('App.MyOrganizationDocument', {
    file: {embedded: 'load'}
});


App.Organization = DS.Model.extend({
    url: 'organizations',
    name: DS.attr('string'),
    description: DS.attr('string', {defaultValue: ""}),

    // Internet
    website: DS.attr('string', {defaultValue: ""}),
    facebook: DS.attr('string', {defaultValue: ""}),
    twitter: DS.attr('string', {defaultValue: ""}),

    websiteUrl: function(){
        var website = this.get('website');
        if (website) {
            if (website.substr(0, 4) != 'http') {
                return 'http://' + website;
            }
            return website;
        }
        return "";
    }.property('website'),
    facebookUrl: function(){
        var facebook = this.get('facebook');
        if (facebook) {
            if (facebook.substr(0, 4) != 'http') {
                return 'http://' + facebook;
            }
            return facebook;
        }
        return "";
    }.property('facebook'),
    twitterUrl: function(){
        var twitter = this.get('twitter');
        if (twitter) {
            //Assumes input was of the form: @handle (conforming to the placeholder text)
            return 'http://twitter.com/' + twitter.substr(1);

        }
        return "";
    }.property('twitter'),

    // Legal
    legalStatus: DS.attr('string', {defaultValue: ""})
});



App.MyOrganizationDocument = DS.Model.extend({
    url: 'organizations/documents/manage',

    organization: DS.belongsTo('App.MyOrganization'),
    file: DS.attr('file')
});

App.MyOrganization = DS.Model.extend({
    url: 'organizations/manage',
    name: DS.attr('string'),
    description: DS.attr('string', {defaultValue: ""}),

    projects: DS.hasMany('App.MyProject'),

    // Address
    address_line1: DS.attr('string', {defaultValue: ""}),
    address_line2: DS.attr('string', {defaultValue: ""}),
    city: DS.attr('string', {defaultValue: ""}),
    state: DS.attr('string', {defaultValue: ""}),
    country: DS.attr('string'),
    postal_code: DS.attr('string', {defaultValue: ""}),
    phone_number: DS.attr('string', {defaultValue: ""}),

    // Internet
    website: DS.attr('string', {defaultValue: ""}),
    email: DS.attr('string', {defaultValue: ""}),
    facebook: DS.attr('string', {defaultValue: ""}),
    twitter: DS.attr('string', {defaultValue: ""}),
    skype: DS.attr('string', {defaultValue: ""}),

    validProfile: function(){
        if (this.get('name') &&  this.get('description') && this.get('email') &&
              this.get('address_line1') && this.get('city') && this.get('country')
            ){
            return true;
        }
        return false;
    }.property('name', 'description', 'email', 'address_line1', 'city', 'country'),


    // Legal
    legalStatus: DS.attr('string', {defaultValue: ""}),
    documents: DS.hasMany('App.MyOrganizationDocument'),

    validLegalStatus: function(){
        if (this.get('legalStatus') &&  this.get('documents.length') > 0){
            return true;
        }
        return false;
    }.property('legalStatus', 'documents.length'),

    // Bank
    account_bank_name: DS.attr('string', {defaultValue: ""}),
    account_bank_address: DS.attr('string', {defaultValue: ""}),
    account_bank_country: DS.attr('string', {defaultValue: ""}),
    account_iban: DS.attr('string', {defaultValue: ""}),
    account_bic: DS.attr('string', {defaultValue: ""}),
    account_number: DS.attr('string', {defaultValue: ""}),
    account_name: DS.attr('string', {defaultValue: ""}),
    account_city: DS.attr('string', {defaultValue: ""}),
    account_other: DS.attr('string', {defaultValue: ""}),

    validBank: function(){
        if (this.get('account_bank_name') &&  this.get('account_bank_country') && this.get('account_name') && this.get('account_city') && (this.get('account_number') || this.get('account_iban'))){
            return true;
        }
        return false;
    }.property('account_bank_name', 'account_bank_country', 'account_name', 'account_city', 'account_iban', 'account_number')

});


