Ember.FacebookMixin = Ember.Mixin.create({
    FBUser: void 0,
    appId: void 0,
    facebookParams: Ember.Object.create(),
    fetchPicture: true,
    connectError: false,

    init: function() {
        this._super();
        return window.FBApp = this;
    },

    facebookConfigChanged: (function() {
        var _this = this;
        this.removeObserver('appId');

        window.fbAsyncInit = function() {
            return _this.fbAsyncInit();
        };

        return $(function() {
            var js;
            $('body').append($("<div>").attr('id', 'fb-root'));
            js = document.createElement('script');
            
            $(js).attr({
                id: 'facebook-jssdk',
                async: true,
                src: "//connect.facebook.net/en_US/all.js"
            });
            return $('head').append(js);
        });
    }).observes('facebookParams', 'appId'),

    fbAsyncInit: function() {
        var facebookParams,
            _this = this;

        facebookParams = this.get('facebookParams');
        facebookParams = facebookParams.setProperties({
            appId: this.get('appId' || facebookParams.get('appId') || void 0),
            status: facebookParams.get('status') || true,
            cookie: facebookParams.get('cookie') || true,
            xfbml: facebookParams.get('xfbml') || true,
            channelUrl: facebookParams.get('channelUrl') || void 0
        });

        FB.init(facebookParams);

        this.set('FBloading', true);


        FB.Event.subscribe('auth.authResponseChange', function(response) {
            if (typeof _this.appLogin == 'function') {
                _this.appLogin(response.authResponse);
            }
            return _this.updateFBUser(response);
        });

        return FB.getLoginStatus(function(response) {
            if (response.status === 'connected') {
                if (typeof _this.appLogin == 'function') {
                    _this.appLogin(response.authResponse);
                }
            }

            return _this.updateFBUser(response);
        });
    },

    updateFBUser: function(response) {
        var _this = this;

        if (response.status === 'connected') {
            FBApp.set("connectError", false);
            return FB.api('/me', function(user) {

                var FBUser;
                FBUser = Ember.Object.create(user);
                FBUser.set('accessToken', response.authResponse.accessToken);
                FBUser.set('accessToken', response.authResponse.accessToken);
                FBUser.set('expiresIn', response.authResponse.expiresIn);

                if (_this.get('fetchPicture')) {
                    return FB.api('/me/picture', function(resp) {
                        FBUser.picture = resp.data.url;
                        _this.set('FBUser', FBUser);
                        return FB.api('/me/picture?type=large', function(resp) {
                            FBUser.largePicture = resp.data.url;
                            _this.set('FBUser', FBUser);
                            return _this.set('FBloading', false);
                        });
                    });
                } else {
                    _this.set('FBUser', FBUser);
                    return _this.set('FBloading', false);
                }
            });
        } else {
            this.set('FBUser', false);
            return this.set('FBloading', false);
        }
    }
});



Ember.FBView = Ember.View.extend({
   classNames: ['btn', 'btn-facebook', 'btn-iconed', 'fb-login-button'],
   attributeBindings: ['data-scope','data-size'],
//   init: function(){
//       this._super();
//       FB.XFBML.parse();
//   },
   click: function(e){
       var _this = this;
       FB.getLoginStatus(function(response) {
            if (response.status === 'connected') {
                App.appLogin(response.authResponse);
            } else {
               FB.login(function(response){
                  if (response.status === 'connected') {
                    App.appLogin(response.authResponse);
                  }

                  if (response.authResponse == null && response.status == 'unknown'){
                      FBApp.set('connectError', gettext("There was an error connecting Facebook"));
                  }
               }, {scope: 'email,public_profile,user_friends'});
            }
       });
   }
});
