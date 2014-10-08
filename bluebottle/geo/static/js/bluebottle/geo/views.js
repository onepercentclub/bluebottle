App.CountrySelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Country")
});


// CountryView with limited options
App.UsedCountrySelectView = App.CountrySelectView.extend();


App.CountryCodeSelectView = Em.Select.extend({
    content:  [{"code": "0", "name": "--loading--"}],
    optionValuePath: "content.code",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Country")
});


App.ProjectMapPopupView = Em.View.extend({
    templateName: 'project-map-popup'
});

App.UsedCountrySelectViewMixin = Em.Mixin.create({
	setupController: function(model, controller) {
        this._super(model, controller);
        // limit the countries
        App.UsedCountry.find().then(function(list) {
            App.UsedCountrySelectView.reopen({
                content: list
            });
        });
    }
})