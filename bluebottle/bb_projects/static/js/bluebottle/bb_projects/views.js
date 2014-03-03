App.ProjectMembersView = Em.View.extend({
    templateName: 'project_members'
});

App.ProjectSupporterView = Em.View.extend({
    templateName: 'project_supporter',
    tagName: 'li',
    didInsertElement: function(){
        this.$('a').popover({trigger: 'hover', placement: 'top'})
    }
});

App.ProjectSupporterListView = Em.View.extend({
    templateName: 'project_supporter_list'
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


App.ProjectSearchFormView = Em.View.extend({
    templateName: 'project_search_form'
});

App.ProjectView = Em.View.extend({
    templateName: 'project',

    didInsertElement: function(){
        this._super();
        this.$('.tags').popover({trigger: 'hover', placement: 'top', width: '100px'});
        
        // project plan
        var height = $(window).height();
        var width = $(window).width();
        this.$(".project-plan-navigation, .project-plan-main").height(height);
        
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
    },
    staticMap: function(){
        var latlng = this.get('controller.latitude') + ',' + this.get('controller.longitude');
        return "http://maps.googleapis.com/maps/api/staticmap?" + latlng + "&zoom=8&size=600x300&maptype=roadmap" +
            "&markers=color:pink%7Clabel:P%7C" + latlng + "&sensor=false";
    }.property('latitude', 'longitude')    
});

App.ProjectIndexView = Em.View.extend({
    templateName: 'project_wall',
    willInsertElement: function() {
        this.get("controller").getTasks();
        this.get("controller").set("showingAll", false);
    }
});

/* Form Elements */

App.ProjectOrderList = [
    {value: 'title', title: gettext("title")},
    {value: 'money_needed', title: gettext("money needed")},
    {value: 'deadline', title: gettext("deadline")}
];

App.ProjectOrderSelectView = Em.Select.extend({
    content: App.ProjectOrderList,
    optionValuePath: "content.value",
    optionLabelPath: "content.title"
});

App.ProjectPhaseSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a phase")

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
            console.log(this.get('controller.model.values'));
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

App.MyProjectView = Em.View.extend({
    templateName: 'my_project'

});


App.ThemeSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: "Pick a theme"
});

App.UsedThemeSelectView = App.ThemeSelectView.extend();

App.MyProjectView = Em.View.extend({
    templateName: 'my_project'
});

App.MyProjectBasicsView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_basics'
});

App.MyProjectDescriptionView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_description'
});

App.MyProjectDetailsView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_details'
});

App.MyProjectLocationView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_location'
});

App.MyProjectMediaView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_media'
});

App.MyProjectOrganisationView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_organisation'
});

App.MyProjectLegalView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_legal'
});

App.MyProjectAmbassadorsView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_ambassadors'
});

App.MyProjectBankView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_bank'
});

App.MyProjectBudgetView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_budget'
});

App.MyProjectCampaignView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_campaign'
});

App.MyProjectSubmitView = Em.View.extend(App.PopOverMixin, {
    templateName: 'my_project_submit'
});

