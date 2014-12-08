App.MockIdealBankSelectView = Em.Select.extend({
    content:  [
        {"code": "huey", "name": "Huey Duck Bank"},
        {"code": "dewey", "name": "Dewey Duck Bank"},
        {"code": "louis", "name": "Louis Duck Bank"}
    ],
    optionValuePath: "content.code",
    optionLabelPath: "content.name",
    prompt: gettext("Select your bank")

});
