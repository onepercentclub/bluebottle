App.Adapter.map('App.MyOrganization', {
    documents: {embedded: 'load'}
});

App.Adapter.map('App.MyOrganizationDocument', {
    file: {embedded: 'load'}
});


App.Organization = DS.Model.extend({
    url: 'bb_organizations',
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
    url: 'bb_organizations/documents/manage',

    organization: DS.belongsTo('App.MyOrganization'),
    file: DS.attr('file')
});

App.MyOrganization = DS.Model.extend(App.ModelValidationMixin, {
    url: 'bb_organizations/manage',

    requiredOrganizationFields: ['name', 'email', 'phone_number', 'website'],
    // since 'account_bic' is common for European and not European bank account
    // it's base required field, this also avoid a "ping pong" in the bank tab
    requiredBaseBankOrganizationFields: ['account_holder_name', 'account_holder_address', 'account_holder_postal_code',
                                         'account_holder_city', 'account_holder_country', 'validBic'],
    requiredEuropeanBankOrganizationFields: ['validIban'],
    requiredNotEuropeanBankOrganizationFields: ['account_number', 'account_bank_name',
                                                'account_bank_address', 'account_bank_postal_code',
                                                'account_bank_city', 'account_bank_country'],

    init: function () {
    	this._super();

        this.validatedFieldsProperty('validOrganization', this.get('requiredOrganizationFields'));
        this.validatedFieldsProperty('validBaseBankOrganization', this.get('requiredBaseBankOrganizationFields'));
        this.validatedFieldsProperty('validEuropeanBankOrganization', this.get('requiredEuropeanBankOrganizationFields'));
        this.validatedFieldsProperty('validNotEuropeanBankOrganization', this.get('requiredNotEuropeanBankOrganizationFields'));
        
        this.missingFieldsProperty('missingFieldsOrganization', this.get('requiredOrganizationFields'));
        this.missingFieldsProperty('missingFieldsBaseBankOrganization', this.get('requiredBaseBankOrganizationFields'));
        this.missingFieldsProperty('missingFieldsEuropeanBankOrganization', this.get('requiredEuropeanBankOrganizationFields'));
        this.missingFieldsProperty('missingFieldsNotEuropeanBankOrganization', this.get('requiredNotEuropeanBankOrganizationFields'));
    },

    save: function () {
        this.one('becameInvalid', function(record) {
            // Ember-data currently has no clear way of dealing with the state
            // loaded.created.invalid on server side validation, so we transition
            // to the uncommitted state to allow resubmission
            //TODO: review this after upgrading EMBERDATA
            this._cleanFields();
            if (record.get('isNew')) {
                record.transitionTo('loaded.created.uncommitted');
            } else {
                record.transitionTo('loaded.updated.uncommitted');
            }
        });

        return this._super();
    },

    _cleanFields: function() {
        this.set('account_iban', this.get('account_iban').replace(/\s+/g, ''));
    },

    name: DS.attr('string'),

    nameOrDefault: function () {
        return this.get('name') || '-- No Name --';
    }.property('name'),

    description: DS.attr('string', {defaultValue: ""}),
    current_name: DS.attr('string'),
    projects: DS.hasMany('App.MyProject'),

    // Address
    address_line1: DS.attr('string', {defaultValue: ""}),
    address_line2: DS.attr('string', {defaultValue: ""}),
    city: DS.attr('string', {defaultValue: ""}),
    state: DS.attr('string', {defaultValue: ""}),
    country: DS.belongsTo('App.Country'),
    postal_code: DS.attr('string', {defaultValue: ""}),
    phone_number: DS.attr('string', {defaultValue: ""}),

    // Internet
    website: DS.attr('string', {defaultValue: ""}),
    email: DS.attr('string', {defaultValue: ""}),
    facebook: DS.attr('string', {defaultValue: ""}),
    twitter: DS.attr('string', {defaultValue: ""}),
    skype: DS.attr('string', {defaultValue: ""}),

    validIban: function () {
        // Valid account_iban if it has a length and there are no api errors for the account_iban.
        return this.get('account_iban.length') && !this.get('errors.account_iban');
    }.property('account_iban.length', 'errors.account_iban'),

    validBic: function () {
        // Valid account_bic if it has a length and there are no api errors for the account_bic.
        return this.get('account_bic.length') && !this.get('errors.account_bic');
    }.property('account_bic.length', 'errors.account_bic'),

    validProfile: Em.computed.and('name', 'description', 'email', 'address_line1', 'city', 'country'),

    // Legal
    legalStatus: DS.attr('string', {defaultValue: ""}),

    documents: DS.hasMany('App.MyOrganizationDocument'),

    validBank: Em.computed.and('validBaseBankOrganization', 'validBankAccountInfo'),

    validBankAccountInfo: Em.computed.or('validEuropeanBankOrganization', 'validNotEuropeanBankOrganization'),

    hasDocument: Em.computed.gt('documents.length', 0),

    validLegalStatus: Em.computed.and('legalStatus', 'hasDocument'),

    //Account holder
    account_holder_name: DS.attr('string', {defaultValue: ""}),
    account_holder_address: DS.attr('string', {defaultValue: ""}),
    account_holder_postal_code: DS.attr('string', {defaultValue: ""}),
    account_holder_city: DS.attr('string', {defaultValue: ""}),
    account_holder_country: DS.belongsTo('App.Country'),
    
    //Bank details
    account_iban: DS.attr('string', {defaultValue: ""}),
    account_bic: DS.attr('string', {defaultValue: ""}),
    account_number: DS.attr('string', {defaultValue: ""}),
    account_bank_name: DS.attr('string', {defaultValue: ""}),
    account_bank_address: DS.attr('string', {defaultValue: ""}),
    account_bank_postal_code: DS.attr('string', {defaultValue: ""}),
    account_bank_city: DS.attr('string', {defaultValue: ""}),
    account_bank_country: DS.belongsTo('App.Country')
});


