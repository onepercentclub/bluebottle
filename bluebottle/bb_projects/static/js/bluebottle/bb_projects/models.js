/* Embedded properties */

App.Adapter.map('App.Project', {
    owner: {embedded: 'load'},
    country: {embedded: 'load'},
    meta: {embedded: 'load'},
    tags: {embedded: 'load'}
});

App.Adapter.map('App.ProjectPreview', {
    campaign: {embedded: 'load'},
    country: {embedded: 'load'},
    theme: {embedded: 'load'}
});

App.Adapter.map('App.MyProject', {
    budgetLines: {embedded: 'load'},
    tags: {embedded: 'always'},
    extras: {embedded: 'load'}
});

App.Adapter.map('App.PartnerOrganization', {
    projects: {embedded: 'load'}
});

App.Adapter.map('App.ProjectDonation', {
    member: {embedded: 'both'}
});

/* Models */

App.ProjectCountry = DS.Model.extend({
    name: DS.attr('string'),
    subregion: DS.attr('string')
});


App.Project = DS.Model.extend({
    url: 'bb_projects/projects',

    // Model fields
    slug: DS.attr('string'),
    status: DS.belongsTo('App.ProjectPhase'),
    created: DS.attr('date'),

    owner: DS.belongsTo('App.UserPreview'),
    // Basics
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme'),
    tags: DS.hasMany('App.Tag'),

    // Description
    description: DS.attr('string'),
    effects: DS.attr('string'),
    reach: DS.attr('number'),

    // Location
    country: DS.belongsTo('App.Country'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    // Media
    image: DS.attr('image'),
    video_url: DS.attr('string'),
    video_html: DS.attr('string'),

    viewable: DS.attr('boolean'),
    editable: DS.attr('boolean'),

    organization: DS.belongsTo("App.Organization"),

    phaseName: function(){
        return this.get('status').get('name');
    }.property('phaseName'),

    phaseNum: function(){
        return this.get('status').get('sequence');
    }.property('phaseNum'),

    isPhasePlan: Em.computed.lte('phaseNum', 5),

    isPhaseAct: Em.computed.equal('phaseNum', 9),

    isPhaseResults: Em.computed.equal('phaseNum', 8),

    isPhaseCampaign: Em.computed.equal('phaseNum', 6),

    isPhaseNeedsWork: Em.computed.equal('phaseNum', 3),

    isPhasePlanNew: Em.computed.equal('phaseNum', 1),

    getProject: function(){
        return App.Project.find(this.get('id'));
    }.property('id'),

    daysToGo: function(){
        if (!this.get('deadline')) {
            return null;
        }
        var now = new Date();
        var microseconds = this.get('deadline').getTime() - now.getTime();
        return Math.ceil(microseconds / (1000 * 60 * 60 * 24));
    }.property('deadline'),

    overDeadline: function() {
        var now = new Date();
        return now > this.get("deadline");
    }.property('deadline'),
});


App.ProjectPhase = DS.Model.extend({
    url: 'bb_projects/phases',
    name: DS.attr('string'),
    description: DS.attr('string'),
    sequence: DS.attr('number'),
    active: DS.attr('boolean'),
    editable: DS.attr('boolean'),
    viewable: DS.attr('boolean')
});

App.ProjectPreview = App.Project.extend({
    url: 'bb_projects/previews',
    image: DS.attr('string'),
    country: DS.belongsTo('App.ProjectCountry'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme')
});


App.ProjectSearch = DS.Model.extend({

    text: DS.attr('string'),
    country: DS.attr('number'),
    theme:  DS.attr('number'),
    ordering: DS.attr('string', {defaultValue: 'popularity'}),
    phase: DS.attr('string', {defaultValue: 'campaign'}),
    page: DS.attr('number', {defaultValue: 1})

});

// TODO: Refactor App.DonationPreview to ProjectSupporter
App.DonationPreview = DS.Model.extend({
    url: 'bb_projects/supporters',

    project: DS.belongsTo('App.ProjectPreview'),
    member: DS.belongsTo('App.UserPreview'),
    date_donated: DS.attr('date'),

    time_since: function(){
        return Globalize.format(this.get('date_donated'), 'X');
    }.property('date_donated')
});


App.ProjectDonation = DS.Model.extend({
    url: 'bb_projects/donations',

    member: DS.belongsTo('App.UserPreview'),
    amount: DS.attr('number'),
    date_donated: DS.attr('date'),

    time_since: function(){
        return Globalize.format(this.get('date_donated'), 'X');
    }.property('date_donated')
});



App.Theme = DS.Model.extend({
    url: 'bb_projects/themes',
    name: DS.attr('string')
});


App.UsedTheme = App.Theme.extend({
    url: 'bb_projects/used_themes'
});

/* Project Manage Models */

App.MyProjectBudgetLine = DS.Model.extend({
    url: 'bb_projects/budgetlines/manage',

    project: DS.belongsTo('App.MyProject'),
    description: DS.attr('string'),
    amount: DS.attr('number')
});


App.BudgetLine = DS.Model.extend({
    project: DS.belongsTo('App.Project'),
    description: DS.attr('string'),
    amount: DS.attr('number')
});


App.MyProject = App.Project.extend({
    url: 'bb_projects/manage',

    country: DS.belongsTo('App.Country'),

    validBasics: function(){
        if (this.get('title') &&  this.get('pitch') && this.get('theme') && this.get('tags.length')){
            return true;
        }
        return false;
    }.property('title', 'pitch', 'theme', 'tags.length'),

    validDescription: function(){
        if (this.get('description') && this.get('reach')){
            return true;
        }
        return false;
    }.property('description', 'reach'),


    validLocation: function(){
        if (this.get('country') &&  this.get('latitude') && this.get('longitude')){
            return true;
        }
        return false;
    }.property('country', 'latitude', 'longitude'),


    validMedia: function(){
        if (this.get('image')){
            return true;
        }
        return false;
    }.property('image'),


    created: DS.attr('date'),

    organization: DS.belongsTo('App.MyOrganization'),

    canSubmit: function(){
        if (!this.get('status')) {
            return true;
        }
        if (this.get('isPhasePlanNew')) {
            return true;
        }
        if (this.get('isPhaseNeedsWork')) {
            return true;
        }
        return false;
    }.property('status')

});
