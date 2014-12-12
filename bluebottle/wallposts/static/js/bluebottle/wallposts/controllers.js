App.WallControllerMixin = Em.Mixin.create({
    _setOwnerHasWallposts: function() {
        var _this = this
        if (! this.get('wallpostList.length')) {
            this.set('ownerHasWallposts', false);
            return;
        }
        
        this.get('wallpostList').forEach(function(post){
            if (_this.get('isOwner')) {
                if (post.get('author.username') == _this.get('currentUser.username') && post.get('type') != 'system') {
                    _this.set('ownerHasWallposts', true);
                }
            }                    
        });     
    }.observes('wallpostList.length')
});