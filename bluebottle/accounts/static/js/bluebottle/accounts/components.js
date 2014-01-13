
App.BbMultipleSelectedItemsComponent = Ember.Component.extend({
	itemSelected: function(){
		console.log("itemSelected");
		console.log(this.get("selectedItem"));
		var item = App.Skill.find(this.get("selectedItem") );
		this.get("selectedItems").addObject(item);

	}.observes("selectedItem"),

	actions: {
		removeItem: function(item){
			console.log("item clicked");
			console.log(item);
			console.log(this.get("selectedItems").toString());
			this.get("selectedItems").removeObject(item);
		}
	}
});
