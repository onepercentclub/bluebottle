App.FundRaiserView = Em.View.extend({
    templateName: 'fundRaiser'
});


App.FundRaiserNewView = Em.View.extend({
    templateName: 'fundraiser_new'
});


App.FundRaiserEditView = Em.View.extend({
    templateName: 'fundraiser_edit'
});


App.ProjectFundRaiserListView = Em.View.extend({
    templateName: 'project_fundraiser_list'
});

App.ProjectFundRaiserPopupView = Em.View.extend({
    templateName : 'project_fundraiser_popup'
});

App.ProjectFundRaiserView = Em.View.extend({
	templateName: 'project_fundraiser',
})


App.FundRaiserSupporterListView = Em.View.extend({
    templateName: 'fundraiser_supporter_list'
});

App.FundRaiserDeadLineDatePicker = App.DatePicker.extend({
    config: {minDate: 0, maxDate: "+6M"}
});


App.FundRaiserDonationListView = Em.View.extend({
    templateName: 'fundraiser_donation_list'
});

App.MyFundRaiserListView = Em.View.extend({
    templateName: 'my_fundraiser_list'
});
//
//
// TODO: Unused at this time.
//App.MyFundRaiserView = Em.View.extend({
//    templateName: 'my_fund_raiser'
//});

App.ProjectFundRaiserAllView = Em.View.extend({
    templateName: 'project_fundraiser_all'

});