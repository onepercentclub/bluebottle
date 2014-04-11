/* Embedded properties */

App.Adapter.map('App.Project', {
    owner: {embedded: 'load'},
    country: {embedded: 'load'},
    meta: {embedded: 'load'},
    tags: {embedded: 'load'}
});

App.Adapter.map('App.ProjectPreview', {
    country: {embedded: 'load'},
    theme: {embedded: 'load'}
});

App.Adapter.map('App.MyProject', {
    budgetLines: {embedded: 'load'},
    tags: {embedded: 'always'}
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

    // Start
    language: DS.belongsTo('App.Language'),

    // Pitch
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme'),
    tags: DS.hasMany('App.Tag'),

    // Story
    description: DS.attr('string'),
    effects: DS.attr('string'),
    reach: DS.attr('number'),

    // Location
    country: DS.belongsTo('App.Country'),
    latitude: DS.attr('string', {defaultValue: 54}),
    longitude: DS.attr('string', {defaultValue: 4}),

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
        if (this.get('status') == null){
            return 1;
        }
        return this.get('status').get('sequence');
    }.property('phaseNum'),

    isPhasePlan: Em.computed.lte('phaseNum', 5),

    isPhaseAct: Em.computed.equal('phaseNum', 9),

    isPhaseResults: Em.computed.equal('phaseNum', 8),

    isPhaseCampaign: Em.computed.equal('phaseNum', 6),

    isPhaseNeedsWork: Em.computed.equal('phaseNum', 3),

    isPhasePlanNew: Em.computed.equal('phaseNum', 1),

    isPhaseSubmitted: Em.computed.equal('phaseNum', 2),

    getProject: function(){
        return App.Project.find(this.get('id'));
    }.property('id'),

    //those two function are based on fields which are not implemented here
    //they shouldn't be here, or deadline should be here
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

    cleanTags: function(){
        // Ugly fix to avoid putting tags
        this.get('tags').forEach(function (tag) {
            if (tag.get('isDirty')){
                tag.transitionTo('loaded.updated.saved');
            }
        });
    }.observes('isDirty')
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


App.MyProject = App.Project.extend(App.ModelValidationMixin, {
    url: 'bb_projects/manage',
    
    requiredStoryFields: ['description', 'reach'],
    requiredPitchFields: ['title', 'pitch', 'theme', 'tags.length', 'country', 'latitude', 'longitude'],
    friendlyFieldNames: null,



    init: function () {
        this._super();

        this.validatedFieldsProperty('validStory', this.get('requiredStoryFields'));
        this.validatedFieldsProperty('validPitch', this.get('requiredPitchFields'));

        this.missingFieldsProperty('missingFieldsStory', this.get('requiredStoryFields'));
        this.missingFieldsProperty('missingFieldsPitch', this.get('requiredPitchFields'));
    },

    save: function () {
        this.one('becameInvalid', function(record) {
            // Ember-data currently has no clear way of dealing with the state
            // loaded.created.invalid on server side validation, so we transition
            // to the uncommitted state to allow resubmission
            if (record.get('isNew')) {
                record.transitionTo('loaded.created.uncommitted');
            } else {
                record.transitionTo('loaded.updated.uncommitted');
            }
        });

        this._super();
    },

    valid: function(){
        return (this.get('') && this.get('validPitch'));
    }.property('validStory', 'validPitch'),

    organization: DS.belongsTo('App.MyOrganization'),
    currentUser: DS.belongsTo('App.CurrentUser'),

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
