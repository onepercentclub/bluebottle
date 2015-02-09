Factory.define('suggestion', { 
    
    title: 'Correlian',
    pitch: 'Raid the cantina',
    deadline: function(app) { return new Date(2120, 12, 1);},
    //theme: 'Ewok fest',
    destination: 'Endor',
    org_name: 'Hapes Consortium',
    org_contactname: 'Jabba',
    org_phone: '555-4312',
    org_website: 'www.hapes.com',
    status: 'unconfirmed',

    project: function() {
        return attr('project')
    }
});
