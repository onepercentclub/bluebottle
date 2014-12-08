App.Country = DS.Model.extend({
    url: "geo/countries",
    name: DS.attr('string'),
    code: DS.attr('string'),
    oda: DS.attr('boolean')
});

App.UsedCountry = App.Country.extend({
	url: "geo/used_countries"
});
