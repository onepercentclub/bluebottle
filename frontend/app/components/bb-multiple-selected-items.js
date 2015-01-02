App.BbMultipleSelectedItemsComponent = Ember.Component.extend({
    itemSelected: function(){
        var type = this.get("type");
        var obj = App[type];
        var item = obj.find(this.get("selectedItem") );
        this.get("selectedItems").addObject(item);


    }.observes("selectedItem"),

    actions: {
        removeItem: function(item){
            this.get("selectedItems").removeObject(item);
        }
    }
});
