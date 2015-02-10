App.ProjectMembersView = Em.View.extend({
    templateName: 'project_members'
});

App.ProjectDonationView = Em.View.extend({
    templateName: 'project_donation'
});

App.ProjectListView = Em.View.extend(App.ScrollInView, {
    templateName: 'project_list'
});

App.ProjectPreviewView = Em.View.extend({
    templateName: 'project_preview'
});

App.ProjectPreviewListView = Em.View.extend({
    templateName: 'project_preview_list'
});

App.ProjectSearchInput = Em.TextField.extend({
    placeholder: gettext('Search')
});

App.ProjectSearchFormView = Em.View.extend({
    templateName: 'project_search_form'
});

App.ProjectView = Em.View.extend({
    templateName: 'project',

    didInsertElement: function(){
        this._super();
        this.$('.tags').popover({trigger: 'hover', placement: 'top', width: '100px'});       
    } 
});

App.ProjectPlanView = Em.View.extend({
    templateName: 'project_plan',

    didInsertElement: function(){
        // project plan
        //var height = $(window).height();
        //var width = $(window).width();
        //this.$(".project-plan-navigation, .project-plan-main").height(height+60);
        
        var view = this;
        view.$(".project-plan-main-link:first").addClass("active");

        // TODO: Solve the extra scrollbar on the html body
        view.$(".project-plan-link").click(function(event) {
          view.$("#project-plan").addClass("active");
          event.preventDefault();
        });
        view.$(".project-plan-back-link").click(function(event) {
          view.$("#project-plan").removeClass("active");
          event.preventDefault();
        });
        view.$(".project-plan-main-link").click(function(event) {
            view.$(".project-plan-main").scrollTo($(this).attr("href"), {duration: 300});
            view.$(".project-plan-main-link.active").removeClass("active");
            view.$(event.target).addClass("active");
            event.preventDefault();
        }); 
    }
});

/* Form Elements */

App.ProjectPhaseSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Phase")

});

App.ProjectPhaseChoiceView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Phase")

});

App.GenericFieldView = Em.View.extend({
    templateName: function(){
        if (this.get('controller.model.type') == 'textarea') {
            return 'generic_textarea';
        }
        if (this.get('controller.model.type') == 'text') {
            return 'generic_text';
        }
        if (this.get('controller.model.type') == 'radio') {
            return 'generic_radio';
        }
        if (this.get('controller.model.type') == 'select') {
            return 'generic_select';
        }
        return 'generic_textarea';

    }.property('controller.model.type'),

    value: function(){
        return this.get('controller.extras').firstObject.get('value');
    }.property('controller.extras', 'controller.model.id')

});

/*
 Project Manage Views
 */


App.MyProjectListView = Em.View.extend({
    templateName: 'my_project_list'
});

App.ThemeSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Theme")
});

App.UsedThemeSelectView = App.ThemeSelectView.extend();

App.MyProjectView = Em.View.extend({
    templateName: 'my_project'
});

App.MyProjectPitchView = Em.View.extend({
    templateName: 'my_project_pitch'
});

App.MyProjectStoryView = Em.View.extend({
    templateName: 'my_project_story'
});

App.MyProjectDetailsView = Em.View.extend({
    templateName: 'my_project_details'
});

App.MyProjectLocationView = Em.View.extend({
    templateName: 'my_project_location'
});

App.MyProjectMediaView = Em.View.extend({
    templateName: 'my_project_media'
});

App.MyProjectOrganisationView = Em.View.extend({
    templateName: 'my_project_organisation',

    actions: {
        addFile: function (file) {
            this.get('controller').send('addFile', file);
        }
    },

    focusNameField: function () {
        // If there is already a focused element then don't 
        // auto focus the first one
        if (this.$('input:focus'))
            return;

        var nameInput = this.$('input:first');
        if (nameInput)
            nameInput.focus();
    }.observes('controller.model.isNew')
});

App.MyProjectAmbassadorsView = Em.View.extend({
    templateName: 'my_project_ambassadors'
});

App.MyProjectBankView = Em.View.extend(Em.TargetActionSupport, {
    templateName: 'my_project_bank'
});

App.MyProjectBudgetView = Em.View.extend({
    templateName: 'my_project_budget'
});

App.MyProjectCampaignView = Em.View.extend({
    templateName: 'my_project_campaign'
});

App.MyProjectSubmitView = Em.View.extend({
    templateName: 'my_project_submit'
});


App.ProjectDonationListView = Em.View.extend({
    templateName: 'project_donation_list'
});


