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
        {'id':'visa', 'name': 'Visa Card'},
        {'id':'mastercard', 'name': 'Master Card'},
    ],
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Select your credit card")

});

App.DocdataCreditcardView = Em.View.extend({
    templateName: 'docdataCreditcard',

    didInsertElement: function() {
        $('.card-types-list label').on('click', function(e) {
            $('.card-types-list label').removeClass('is-active');
            $(this).addClass('is-active');
        });
    }
});
