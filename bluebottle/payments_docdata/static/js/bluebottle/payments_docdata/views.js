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

App.DocdataDirectdebitView = Em.View.extend({
    templateName: 'docdataDirectdebit',

    didInsertElement: function() {
        var accountNumber = this.$().find('#accountnumber');
        accountNumber.on('keyup', function(){
            var accountNumberVal = accountNumber.val(),
                bic = $('.bic-col'),
                iban = $('.iban-col');
            if (accountNumberVal.length >= 2) {
                if (accountNumberVal.indexOf('NL') > - 1) {
                    bic.hide({
                        duration: 200,
                        specialEasing: 'fadeout',
                        complete: function() {
                            iban.attr('class', 'col12 iban-col');
                        }
                    });
                } else {
                    iban.attr('class', 'col8 iban-col');
                    bic.show({
                        duration: 300,
                        specialEasing: 'fadein'
                    });
                }
            }
        });
    }
})
