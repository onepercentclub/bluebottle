App.Adapter.map('App.Project', {
    owner: {embedded: 'load'},
    campaign: {embedded: 'load'},
    plan: {embedded: 'load'},
    country: {embedded: 'load'}
});
App.Adapter.map('App.ProjectPreview', {
    campaign: {embedded: 'load'},
    country: {embedded: 'load'}
});

App.Adapter.map('App.ProjectPlan', {
    tags: {embedded: 'load'},
    country: {embedded: 'load'}
});
App.Adapter.map('App.ProjectPitch', {
    tags: {embedded: 'load'},
    country: {embedded: 'load'}
});
App.Adapter.map('App.MyProjectPlan', {
    ambassadors: {embedded: 'load'},
    budgetLines: {embedded: 'load'},
    tags: {embedded: 'always'}
});
App.Adapter.map('App.MyProjectPitch', {
    tags: {embedded: 'always'}
});
App.Adapter.map('App.MyOrganization', {
    addresses: {embedded: 'both'},
    documents: {embedded: 'load'}
});
App.Adapter.map('App.MyOrganizationDocument', {
    file: {embedded: 'load'}
});
App.Adapter.map('App.PartnerOrganization', {
    projects: {embedded: 'load'}
});

App.Organization = DS.Model.extend({
    url: 'organizations',
    name: DS.attr('string'),
    description: DS.attr('string', {defaultValue: ""}),

    // Internet
    website: DS.attr('string', {defaultValue: ""}),
    facebook: DS.attr('string', {defaultValue: ""}),
    twitter: DS.attr('string', {defaultValue: ""}),
    skype: DS.attr('string', {defaultValue: ""}),

    // Legal
    legalStatus: DS.attr('string', {defaultValue: ""})
});


App.ProjectCountry = DS.Model.extend({
    name: DS.attr('string'),
    subregion: DS.attr('string')
});


App.ProjectPitch = DS.Model.extend({
    url: 'projects/pitches',

    project: DS.belongsTo('App.MyProject'),
    created: DS.attr('date'),
    status: DS.attr('string'),

    // Basics
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.attr('string'),
    tags: DS.hasMany('App.Tag'),
    description: DS.attr('string'),
    need: DS.attr('string'),

    // Location
    country: DS.belongsTo('App.ProjectCountry'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    // Media
    image: DS.attr('string'),
    image_small: DS.attr('string'),
    image_square: DS.attr('string'),
    image_bg: DS.attr('string')

});


App.ProjectPlan = DS.Model.extend({
    url: 'projects/plans',

    project: DS.belongsTo('App.MyProject'),
    status: DS.attr('string'),
    created: DS.attr('date'),

    // Basics
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme'),
    need: DS.attr('string'),
    tags: DS.hasMany('App.Tag'),

    // Description
    description: DS.attr('string'),
    effects: DS.attr('string'),
    future: DS.attr('string'),
    for_who: DS.attr('string'),
    reach: DS.attr('number'),

    // Location
    country: DS.belongsTo('App.ProjectCountry'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    // Media
    image: DS.attr('image'),

    // Organization
    organization: DS.belongsTo('App.Organization')

});


App.ProjectCampaign = DS.Model.extend({
    url: 'projects/plans',

    project: DS.belongsTo('App.MyProject'),
    status: DS.attr('string'),
    money_asked: DS.attr('number'),
    money_donated: DS.attr('number'),
    deadline: DS.attr('date'),

    daysToGo: function(){
        var now = new Date();
        var microseconds = this.get('deadline').getTime() - now.getTime();
        return Math.ceil(microseconds / (1000 * 60 * 60 * 24));
    }.property('deadline'),

    money_needed: function(){
        var donated = this.get('money_asked') - this.get('money_donated');
        if (donated < 0) {
            return 0;
        }
        return Math.ceil(donated);
    }.property('money_asked', 'money_donated')
});


App.Project = DS.Model.extend({
    url: 'projects/projects',

    // Model fields
    slug: DS.attr('string'),
    title: DS.attr('string'),
    phase: DS.attr('string'),
    created: DS.attr('date'),

    plan: DS.belongsTo('App.ProjectPlan'),
    campaign: DS.belongsTo('App.ProjectCampaign'),

    owner: DS.belongsTo('App.UserPreview'),
    coach: DS.belongsTo('App.UserPreview'),

    days_left: DS.attr('number'),
    supporters_count: DS.attr('number'),

    wallposts: DS.hasMany('App.WallPost'),

    taskCount: DS.attr('number'),

    isPhasePlan: Em.computed.equal('phase', 'plan'),
    isPhaseCampaign: Em.computed.equal('phase', 'campaign'),
    isPhaseAct: Em.computed.equal('phase', 'act'),
    isPhaseResults: Em.computed.equal('phase', 'results'),
    isPhaseRealized: Em.computed.equal('phase', 'realized'),
    isPhaseFailed: Em.computed.equal('phase', 'failed'),

    getProject: function(){
        return App.Project.find(this.get('id'));
    }.property('id')


});


App.ProjectPreview = App.Project.extend({
    url: 'projects/previews',
    image: DS.attr('string'),
    country: DS.belongsTo('App.ProjectCountry'),
    description: DS.attr('string')
});


App.ProjectSearch = DS.Model.extend({

    text: DS.attr('string'),
    country: DS.attr('number'),
    theme:  DS.attr('number'),
    ordering: DS.attr('string', {defaultValue: 'popularity'}),
    phase: DS.attr('string', {defaultValue: 'campaign'}),
    page: DS.attr('number', {defaultValue: 1})

});


App.DonationPreview =  DS.Model.extend({
    url: 'projects/donations',

    project: DS.belongsTo('App.ProjectPreview'),
    member: DS.belongsTo('App.UserPreview'),
    date_donated: DS.attr('date'),

    time_since: function(){
        return Globalize.format(this.get('date_donated'), 'X');
    }.property('date_donated')
});


/* Project Manage Models */

/*
 Models
 */

App.AddressTypeSelectView = Em.Select.extend({
    content: [
        {value: 'physical', title: "Physical address"},
        {value: 'postal', title: "Postal address"},
        {value: 'other', title: "Other address"}
    ],
    optionValuePath: "content.value",
    optionLabelPath: "content.title"
});


App.MyOrganizationAddress = DS.Model.extend({
    url: 'organizations/addresses/manage',

    organization: DS.belongsTo('App.MyOrganization'),
    line1: DS.attr('string', {defaultValue: ""}),
    line2: DS.attr('string', {defaultValue: ''}),
    postal_code: DS.attr('string', {defaultValue: ""}),
    city: DS.attr('string', {defaultValue: ""}),
    country: DS.attr('string', {defaultValue: ""}),
    type: DS.attr('string', {defaultValue: 'physical'}),

    validAddress: function(){
        if (this.get('line1') &&  this.get('city') && this.get('country')){
            return true;
        }
        return false;
    }.property('line1', 'city', 'country')

});

App.MyOrganizationDocument = DS.Model.extend({
    url: 'organizations/documents/manage',

    organization: DS.belongsTo('App.MyOrganization'),
    file: DS.attr('file')
});

App.MyProjectAmbassador = DS.Model.extend({
    url: 'projects/ambassadors/manage',

    project_plan: DS.belongsTo('App.MyProjectPlan'),
    name: DS.attr('string'),
    email: DS.attr('string'),
    description: DS.attr('string')
});

App.MyProjectBudgetLine = DS.Model.extend({
    url: 'projects/budgetlines/manage',

    project_plan: DS.belongsTo('App.MyProjectPlan'),
    description: DS.attr('string'),
    amount: DS.attr('number')
});

App.MyOrganization = DS.Model.extend({
    url: 'organizations/manage',
    name: DS.attr('string'),
    description: DS.attr('string', {defaultValue: ""}),

    // Internet
    website: DS.attr('string', {defaultValue: ""}),
    email: DS.attr('string', {defaultValue: ""}),
    facebook: DS.attr('string', {defaultValue: ""}),
    twitter: DS.attr('string', {defaultValue: ""}),
    skype: DS.attr('string', {defaultValue: ""}),

    // Addresses
    addresses: DS.hasMany('App.MyOrganizationAddress'),

    validProfile: function(){
        if (this.get('name') &&  this.get('description') && this.get('email') && this.get('addresses.firstObject.validAddress')){
            return true;
        }
        return false;
    }.property('name', 'description', 'email', 'addresses.firstObject.validAddress'),


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


App.MyProjectPitch = DS.Model.extend({
    url: 'projects/pitches/manage',

    project: DS.belongsTo('App.MyProject'),

    // Basics
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.attr('string'),
    tags: DS.hasMany('App.Tag'),
    description: DS.attr('string'),
    need: DS.attr('string'),

    validBasics: function(){
        if (this.get('title') &&  this.get('pitch') && this.get('description') &&
            this.get('theme') && this.get('tags.length') && this.get('need')){
            return true;
        }
        return false;
    }.property('title', 'pitch', 'theme', 'tags', 'description', 'theme', 'need'),


    // Location
    country: DS.attr('string'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    validLocation: function(){
        if (this.get('country') &&  this.get('latitude') && this.get('longitude')){
            return true;
        }
        return false;
    }.property('country', 'latitude', 'longitude'),


    // Media
    image: DS.attr('image'),

    validMedia: function(){
        if (this.get('image')){
            return true;
        }
        return false;
    }.property('image'),

    // Submitting
    status: DS.attr('string'),
    agreed: DS.attr('boolean'),

	isBeingReviewed: function(){
        if (this.get('status') == 'reviewed') {
            return true;
        }
        return false;
	}.property('status'),

    created: DS.attr('date')
});



App.MyProjectPlan = DS.Model.extend({
    url: 'projects/plans/manage',

    project: DS.belongsTo('App.MyProject'),

    // Basics
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.attr('string'),
    need: DS.attr('string'),
    tags: DS.hasMany('App.Tag'),


    needsFunding: function (){
        if (this.get('need') == 'finance' || this.get('need') == 'both') {
            return true;
        }
        return false;
    }.property('need'),

    validBasics: function(){
        if (this.get('title') &&  this.get('pitch') && this.get('theme') && this.get('need') && this.get('tags.length')){
            return true;
        }
        return false;
    }.property('title', 'pitch', 'theme', 'tags', 'slug'),

    // Description
    description: DS.attr('string'),
    effects: DS.attr('string'),
    future: DS.attr('string'),
    forWho: DS.attr('string'),
    reach: DS.attr('number'),

    validDescription: function(){
        if (this.get('description') &&  this.get('effects') && this.get('future') && this.get('forWho') && this.get('reach')){
            return true;
        }
        return false;
    }.property('description', 'effects', 'future', 'for_who', 'reach'),


    // Location
    country: DS.attr('string'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    validLocation: function(){
        if (this.get('country') &&  this.get('latitude') && this.get('longitude')){
            return true;
        }
        return false;
    }.property('country', 'latitude', 'longitude'),

    // Media
    image: DS.attr('image'),

    validMedia: function(){
        if (this.get('image')){
            return true;
        }
        return false;
    }.property('image'),

    // Organization
    organization: DS.belongsTo('App.MyOrganization'),

    // Ambassadors
    ambassadors: DS.hasMany('App.MyProjectAmbassador'),

    validAmbassadors: function(){
        if (this.get('ambassadors.length') > 2) {
            return true;
        }
        return false;
    }.property('ambassadors.length'),

    // Submitting
    status: DS.attr('string'),

    // Crowd funding
    moneyNeeded: DS.attr('string'),
    campaign: DS.attr('string'),

    validCampaign: function(){
        if (this.get('moneyNeeded') &&  this.get('campaign')){
            return true;
        }
        return false;
    }.property('moneyNeeded', 'campaign'),

    // Budget
    budgetLines: DS.hasMany('App.MyProjectBudgetLine'),

    totalBudget: function(){
        var lines = this.get('budgetLines');
        return lines.reduce(function(prev, line){
            return (prev || 0) + (line.get('amount')/1 || 0);
        });
    }.property('budgetLines.@each.amount'),

    validBudget: function(){
        if (this.get('totalBudget') > 0 &&  this.get('totalBudget') <= 5000 ){
            return true;
        }
        return false;
    }.property('totalBudget'),


    created: DS.attr('date')
});


App.MyProjectCampaign = App.ProjectCampaign.extend({
    url: 'projects/campaigns/manage',

    project: DS.belongsTo('App.MyProject'),
    status: DS.attr('string'),
    moneyAsked: DS.attr('number'),
    moneyDonated: DS.attr('number'),
    deadline: DS.attr('date')

});


App.MyProject = DS.Model.extend({
    url: 'projects/manage',

    // Model fields
    slug: DS.attr('string'),
    title: DS.attr('string'),
    phase: DS.attr('string'),

    pitch: DS.belongsTo('App.MyProjectPitch'),
    plan: DS.belongsTo('App.MyProjectPlan'),
    campaign: DS.belongsTo('App.MyProjectCampaign'),

    coach: DS.belongsTo('App.User'),

    getProject: function(){
        return App.Project.find(this.get('id'));
    }.property('id'),

    isPhasePitch: Em.computed.equal('phase', 'pitch'),
    isPhasePlan: Em.computed.equal('phase', 'plan'),
    isPhaseCampaign: Em.computed.equal('phase', 'campaign'),
    isPhaseAct: Em.computed.equal('phase', 'act'),
    isPhaseResults: Em.computed.equal('phase', 'results'),

    isPublic: function(){
        if (this.get('phase') == 'pitch') {
            return false;
        }
        if (this.get('phase') == null) {
            return false;
        }
        return true;
    }.property('phase'),


    inProgress: function(){
        var phase = this.get('phase');
        if (phase == 'realized') {
            return false;
        }
        if (phase == 'failed') {
            return false;
        }
        return true;
    }.property('phase', 'pitch.status', 'plan.status')

});

