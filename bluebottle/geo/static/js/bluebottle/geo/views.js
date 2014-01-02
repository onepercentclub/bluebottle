App.CountrySelectView = Em.Select.extend({
    content:  [{"id": "0", "name": "--loading--"}],
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a country")
});


App.CountryCodeSelectView = Em.Select.extend({
    content:  [{"code": "0", "name": "--loading--"}],
    optionValuePath: "content.code",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a country")
});


App.ProjectCountrySelectView = Em.Select.extend({
    content:  [{"id": "0", "name": "--loading--"}],
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a country")
});

