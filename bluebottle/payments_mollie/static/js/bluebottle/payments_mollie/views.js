App.MollieIdealBankSelectView = Em.Select.extend({
    content:  [
        {'id': 'ideal_TESTNL99',
         'name': 'Test Bank Mollie'}
    ],
    optionValuePath: "content.code",
    optionLabelPath: "content.name",
    prompt: gettext("Select your bank")

});
