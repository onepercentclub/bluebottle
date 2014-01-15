App.CountrySelectView = Em.Select.extend({
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
