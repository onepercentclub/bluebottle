App.DocdataIdealBankSelectView = Em.Select.extend({
    content:  [
        {'id':'ABNANL2A', 'name': 'ABN Amro Bank'},
        {'id':'ASNBNL21', 'name': 'ASN Bank'},
        {'id':'FRBKNL2L', 'name': 'Friesland Bank'},
        {'id':'INGBNL2A', 'name': 'ING Bank'},
        {'id':'KNABNL2H', 'name': 'Knab'},
        {'id':'FVLBNL22', 'name': 'van Lanschot Bankiers'},
        {'id':'RABONL2U', 'name': 'Rabobank'},
        {'id':'RBRBNL21', 'name': 'Regio Bank'},
        {'id':'TRIONL2U', 'name': 'Triodos Bank'},
        {'id':'SNSBNL2A', 'name': 'SNS Bank'},
    ],
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Select your bank")
});


App.DocdataCreditcardSelectView = Em.Select.extend({
    content:  [
        {'id':'amex', 'name': 'American Express'},
        {'id':'visa', 'name': 'Visa Card'},
        {'id':'mastercard', 'name': 'Master Card'},
    ],
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Select your credit card")
});

App.DocdataDirectdebitView = Em.View.extend({
    templateName: 'docdataDirectdebit',

    didInsertElement: function() {
        var accountNumber = this.$().find('#accountnumber'),
            bic = this.$().find('#bicswift');

        $(accountnumber).on('keyup', function() {
            if ($(accountnumber).val() === '') {
                bic.removeAttr('disabled');
            } else {
                bic.attr('disabled', 'disabled');
            }
        });
    }
})
