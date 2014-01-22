App = Em.Application.create({
    VERSION: '1.0.0',

    // TODO: Remove this in production builds.
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
        App.CurrentUser.find('current').then(
            function(user){
                var primaryLanguage = user.get('primary_language');
                if (primaryLanguage && primaryLanguage != language) {
                    document.location = '/' + primaryLanguage + document.location.hash;
                }
            },
            function(data){
                // FOr now redirect all visitors that are not authenticated.
                document.location = '/token/missing';
            }
        );

        // We don't have to check if it's one of the languages available. Django will have thrown an error before this.
        this.set('language', language);

        // Now that we know the language we can load the handlebars templates.
        //this.loadTemplates(this.templates);

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

        this.setLocale(locale);
        this.initSelectViews();
    },

    initSelectViews: function() {
        // Pre-load these lists so we avoid race conditions when displaying forms
        App.Country.find().then(function(list) {
            App.CountrySelectView.reopen({
                content: list
            });
            App.CountryCodeSelectView.reopen({
                content: list
            });
        });

        App.Theme.find().then(function(list) {
            App.ThemeSelectView.reopen({
                content: list
            });
        });

        App.Skill.find().then(function(list) {
            App.SkillSelectView.reopen({
                content: list
            });
        });

        App.ProjectPhase.find().then(function(data){

            var list = App.ProjectPhase.filter(function(item){return item.get('viewable');});

            App.ProjectPhaseSelectView.reopen({
            content: list
            });
        });
    },

    setLocale: function(locale) {
        if (!locale) {
            locale = this.get('locale');
        }

        if (locale != 'en-US') {
            if (locale == 'nl') {
                locale = 'nl-NL';
            }

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

// Mixin to scroll view top top of the screen
App.ScrollInView = Em.Mixin.create({
    didInsertElement: function(a, b){
        var offset = this.$().offset().top - 120;
        var windowOffset = $(window).scrollTop();
        // Only scroll if the focus is more then 50px off.
        if (Math.abs(windowOffset - offset) > 50) {
            $("html, body").animate({ scrollTop: offset }, 600);
        }
    }
});

App.ScrollToTop = Em.Mixin.create({
    afterModel: function(){
        this._super();
        $("html, body").animate({ scrollTop: 0 }, 600);
    }
});


/**
 * The Ember Data Adapter and Store configuration.
 */
App.Adapter = DS.DRF2Adapter.extend({
    namespace: "api",

    plurals: {
        "projects/manage": "projects/manage",
        "projects/pitches/manage": "projects/pitches/manage",
        "projects/plans/manage": "projects/plans/manage",
        "projects/campaigns/manage": "projects/campaigns/manage",
        "projects/wallposts/media": "projects/wallposts/media",
        "projects/wallposts/text": "projects/wallposts/text",
        "organizations/manage": "organizations/manage",
        "organizations/addresses/manage": "organizations/addresses/manage",
        "organizations/documents/manage": "organizations/documents/manage",
        "projects/ambassadors/manage": "projects/ambassadors/manage",
        "projects/budgetlines/manage": "projects/budgetlines/manage",
        "users/activate": "users/activate",
        "users/passwordset": "users/passwordset",
        "homepage": "homepage",
        "contact/contact": "contact/contact"
    }
});

// Assigning plurals for model properties doesn't seem to work with extend, it does this way:
App.Adapter.configure("plurals", {
    "address": "addresses",
    "favourite_country" : "favourite_countries"
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

// Embedded Model Mapping
//
// http://stackoverflow.com/questions/14320925/how-to-make-embedded-hasmany-relationships-work-with-ember-data/14324532#14324532
// The two possible values of embedded are:
//   load: The child records are embedded when loading, but should be saved as standalone records. In order
//         for this to work, the child records must have an ID.
//   always: The child records are embedded when loading, and are saved embedded in the same record. This,
//           of course, affects the dirtiness of the records (if the child record changes, the adapter will
//           mark the parent record as dirty).

App.Store = DS.Store.extend({
    adapter: 'App.Adapter'
});


/* Routing */

App.SlugRouter = Em.Mixin.create({
    serialize: function(model, params) {
        if (params.length !== 1) { return {}; }

        var name = params[0], object = {};
        object[name] = get(model, 'slug');

        return object;
    }
});

App.Router.reopen({
    location: 'hashbang'
});

App.Router.reopen({
    /**
     * Tracks pageviews if google analytics is used
     * Source: http://www.randomshouting.com/2013/05/04/Ember-and-Google-Analytics.html
     */
    didTransition: function(infos) {
        this._super(infos);
        if (window._gaq === undefined) { return; }

        Ember.run.next(function(){
            _gaq.push(['_trackPageview', window.location.hash.substr(1)]);
        });
    }
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
    meta: DS.attr('object')
});

Em.Route.reopen({
    meta_data: function(){
        return this.get('context.meta_data');
    }.property('context.meta_data')
});

App.Router.map(function() {

    this.resource('language', {path:'/:lang'});

    // Fix for Facebook login
    this.route("home", { path: "_=_" });

    this.route("home", { path: "/" });

    this.resource('error', {path: '/error'}, function() {
        this.route('notFound', {path: '/not-found'});
        this.route('notAllowed', {path: '/not-allowed'});
    });

    this.resource('page', {path: '/pages/:page_id'});
    this.resource('contactMessage', {path: '/contact'});

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
            // Close all other modals.
            $('.close-modal').click();

            // Get the controller or create one
            var controller = this.controllerFor(name);
            controller.set('model', context);

            // Get the view. This should be defined.
            var view = App[name.classify() + 'View'].create();
            view.set('controller', controller);

            var modalPaneTemplate = "{{view view.bodyViewClass}}";

            Bootstrap.ModalPane.popup({
                classNames: ['modal', 'large'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view,
                secondary: 'Close'
            });

        },
        openInBox: function(name, context) {
            // Close all other modals.
            $('.close-modal').click();

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
        closeAllModals: function(){
            $('[rel=close]').click();
        },
        showProjectTaskList: function(project_id) {
            var route = this;
            App.Project.find(project_id).then(function(project) {
                route.transitionTo('project', project);
                route.transitionTo('projectTaskList');
            });
        },
        showPage: function(page_id) {
            var route = this;
            App.Page.find(page_id).then(function(page) {
                route.transitionTo('page', page);
                window.scrollTo(0, 0);
            });
        },

        addDonation: function (project) {
            var route = this;
            App.CurrentOrder.find('current').then(function(order) {
                var store = route.get('store');
                var donation = store.createRecord(App.CurrentOrderDonation);
                donation.set('project', project);
                donation.set('order', order);
                donation.save();
                route.transitionTo('currentOrder.donationList');
            });
        }
    },

    urlForEvent: function(actionName, context) {
        return "/nice/stuff"
    }
});


App.UserIndexRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('userProfile');
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
