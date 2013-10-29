Em.TextField.reopen({
    // Update attributeBinding with 'step' and 'multiple'
    attributeBindings: ['type', 'value', 'size', 'step', 'multiple']
});


App = Em.Application.create({
    VERSION: '1.0.0',

    LOG_TRANSITIONS: true,

    // We store language & locale here because they need to be available before loading templates.
    language: 'en',
    locale: 'en-GB',
    interfaceLanguages: [
        Em.Object.create({name:'English', code: 'en'}),
        Em.Object.create({name:'Nederlands', code: 'nl'})
    ],

    ready: function() {
        // Read language string from url.
        var language = window.location.pathname.split('/')[1];
        App.CurrentUser.find('current').then(function(user){ // Throws 404 if not logged in
            var primaryLanguage = user.get('primary_language');
            if (primaryLanguage && primaryLanguage != language) {
                document.location = '/' + primaryLanguage + document.location.hash;
            }
        });
        // We don't have to check if it's one of the languages available. Django will have thrown an error before this.
        this.set('language', language);

        // Read locale from browser with fallback to default.
        var locale = navigator.language || navigator.userLanguage || this.get('locale');
        if (locale.substr(0, 2) != language) {
            // Some overrides to have a sound experience, at least for dutch speaking and dutch based users.

            if (language == 'nl') {
                // For dutch language always overwrite locale. Always use dutch locale.
                locale = 'nl';
            }
            if (language == 'en' && locale.substr(0, 2) == 'nl') {
                // For dutch browser viewing english site overwrite locale.
                // We don't want to have dutch fuzzy dates.
                // If fuzzy dates are translated in other languages we should decide if we want to show those.
                locale = 'en';
            }
        }

        this.initSelectViews();
        this.setLocale(locale);
        this.initSelectViews();
    },

    initSelectViews: function() {
        App.Country.find().then(function(list) { // throws 404 on dev/testing, as expected
            App.CountrySelectView.reopen({
                content: list
            });
            App.CountryCodeSelectView.reopen({
                content: list
            });
        });
        // Get a filtered list of countries that can apply for a project ('oda' countries).
        var filteredList = App.Country.filter(function(item) {return item.get('oda')});

        App.ProjectCountrySelectView.reopen({
            content: filteredList
        });
    },

    setLocale: function(locale) {
        if (!locale) {
            locale = this.get('locale');
        }

        if (locale != 'en-US') {
            // Try to load locale specifications.
            $.getScript('/static/assets/js/vendor/globalize-cultures/globalize.culture.' + locale + '.js')
                .fail(function() {
                    if (window.console) {
                        console.log("No globalize culture file for : "+ locale);
                    }
                    // Specified locale file not available. Use default locale.
                    locale = App.get('locale');
                    Globalize.culture(locale);
                    App.set('locale', locale);
                })
                .success(function() {
                    // Specs loaded. Enable locale.
                    Globalize.culture(locale);
                    App.set('locale', locale);
                });
            $.getScript('/static/assets/js/vendor/jquery-ui/i18n/jquery.ui.datepicker-' + locale.substr(0, 2) + '.js')
                .fail(function() {
                    if (window.console) {
                        console.log("No jquery.ui.datepicker file for : "+ locale);
                    }
                    // Specified locale file not available. Use default locale.
                    locale = App.get('locale');
                    Globalize.culture(locale);
                    App.set('locale', locale);
                })
                .success(function() {
                    // Specs loaded. Enable locale.
                    App.set('locale', locale);
                });
        } else {
            Globalize.culture(locale);
            App.set('locale', locale);
        }
    }
});


App.Adapter = DS.DRF2Adapter.extend({
    namespace: "api",

    plurals: {
        "users/activate": "users/activate",
        "users/passwordset": "users/passwordset",
    }
});


App.Store = DS.Store.extend({
    adapter: 'App.Adapter'
});


App.ApplicationController = Ember.Controller.extend({
    needs: ['currentUser'],
    display_message: false,

    displayMessage: (function() {
        if (this.get('display_message') == true) {
            Ember.run.later(this, function() {
                this.hideMessage();
            }, 10000);
        }
    }).observes('display_message'),

    hideMessage: function() {
        this.set('display_message', false);
    }
});

App.Router.reopen({
    location: 'hashbang'
});

App.Router.reopen({
    didTransition: function(infos) {
        this._super(infos);
        Ember.run.next(function() {
            // the meta module will now go trough the routes and look for data
            App.meta.trigger('reloadDataFromRoutes');
        });
    }
});

DS.Model.reopen({
    meta_data: DS.attr('object')
});

Em.Route.reopen({
    meta_data: function(){
        return this.get('context.meta_data');
    }.property('context.meta_data')
});

App.Router.map(function() {
    this.resource('language', {path:'/:lang'});
    this.route("home", { path: "/" });
});

App.ApplicationRoute = Em.Route.extend({
    actions: {
        selectLanguage: function(language) {
            var user = App.CurrentUser.find('current');
            if (!user.get('id_for_ember')) {
                if (language == App.get('language')) {
                    // Language already set. Don't do anything;
                    return true;
                }
                document.location = '/' + language + document.location.hash;
            }

            App.UserSettings.find(App.CurrentUser.find('current').get('id_for_ember')).then(function(settings){
                if (language == App.get('language')) {
                    // Language already set. Don't do anything;
                    return true;
                }

                if (settings.get('id')) {
                    settings.save();
                }
                var languages = App.get('interfaceLanguages');
                for (i in languages) {
                    // Check if the selected language is available.
                    if (languages[i].code == language) {
                        if (settings.get('id')) {
                            settings.set('primary_language', language);
                        }
                        settings.on('didUpdate', function(){
                            document.location = '/' + language + document.location.hash;
                        });
                        settings.save();
                        return true;
                    }
                }
                language = 'en';
                if (settings.get('id')) {
                    settings.set('primary_language', language);
                }

                settings.on('didUpdate', function(){
                    document.location = '/' + language + document.location.hash;
                });
                settings.save();
                return true;
            });
            return true;
        },

        openInBigBox: function(name, context) {
            // Get the controller or create one
            var controller = this.controllerFor(name);
            controller.set('model', context);

            // Get the view. This should be defined.
            var view = App[name.classify() + 'View'].create();
            view.set('controller', controller);

            var modalPaneTemplate = ['<div class="modal-body"><a class="close" rel="close">&times;</a>{{view view.bodyViewClass}}</div>'].join("\n");

            Bootstrap.ModalPane.popup({
                classNames: ['modal', 'large'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view,
                secondary: 'Close'
            });

        },
        openInBox: function(name, context) {
            // Get the controller or create one
            var controller = this.controllerFor(name);
            if (context) {
                controller.set('model', context);
            }

            // Get the view. This should be defined.
            var view = App[name.classify() + 'View'].create();
            view.set('controller', controller);

            var modalPaneTemplate = ['<div class="modal-body"><a class="close" rel="close">&times;</a>{{view view.bodyViewClass}}</div>'].join("\n");

            Bootstrap.ModalPane.popup({
                classNames: ['modal'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view
            });

        },
    },

    urlForEvent: function(actionName, context) {
        return "/nice/stuff"
    }
});

/* Views */

App.LanguageView = Em.View.extend({
    templateName: 'language',
    classNameBindings: ['isSelected:active'],
    isSelected: function(){
        if (this.get('content.code') == App.language) {
            return true;
        }
        return false;
    }.property('content.code')

});


App.LanguageSwitchView = Em.CollectionView.extend({
    tagName: 'ul',
    classNames: ['nav-language'],
    content: App.interfaceLanguages,
    itemViewClass: App.LanguageView
});


App.ApplicationView = Em.View.extend({
    elementId: 'site'
});

