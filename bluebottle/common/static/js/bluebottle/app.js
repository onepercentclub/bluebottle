Ember.Application.initializer({
    name: 'currentUser',
    after: 'store',

    initialize: function(container, application) {
        var _this = this;

        // delay boot until the current user promise resolves
        App.deferReadiness();

        // Try to fetch the current user
        var currentUser = App.CurrentUser.find('current').then(function(user) {
            // Read language string from url.
            var language = window.location.pathname.split('/')[1];

            // Setup language
            var primaryLanguage = user.get('primary_language');
            primaryLanguage = primaryLanguage.replace('_', '-').toLowerCase();
            if (primaryLanguage && primaryLanguage != language) {
                document.location = '/' + primaryLanguage + document.location.hash;
            }

            // We don't have to check if it's one of the languages available. Django will have thrown an error before this.
            application.set('language', language);

            App.injectUser(container, user);

            // boot the app
            App.advanceReadiness();
        }, function() {
            App.injectUser(container, null);

            container.lookup('controller:application').missingCurrentUser();

            // boot the app without a currect user
            App.advanceReadiness();
        });
    }
});

// A static initializer for app settings
//TODO: we should make it as an ajax request to fetch settings from api
Ember.Application.initializer({
    name: 'appSettings',
    after: 'currentUser',

    initialize: function(container, application) {
        application.set('settings',
            Em.Object.create({
                minPasswordLength: 6,
                minPasswordError: gettext('Password needs to be at least 6 characters long')
            })
        )
    }
});


App = Em.Application.createWithMixins(Em.FacebookMixin, {
    VERSION: '1.0.0',

    // TODO: Remove this in production builds.
    LOG_TRANSITIONS: DEBUG,


    // We store language & locale here because they need to be available before loading templates.
    language: 'en',
    locale: 'en-GB',
    interfaceLanguages: [
        Em.Object.create({name:'English', code: 'en'}),
        Em.Object.create({name:'Nederlands', code: 'nl'})
    ],

    ready: function() {

        // only needed when submitting a form if the user isn't authenticated
        var metaCsrf = $('meta[name=csrf-token]')
        if (metaCsrf)
            this.set('csrfToken', metaCsrf.attr('content'));

        // Read language string from url.
        var language = window.location.pathname.split('/')[1];
        App.CurrentUser.find('current').then(function(user){
            var primaryLanguage = user.get('primary_language');
            if (primaryLanguage && primaryLanguage != language) {
                document.location = '/' + primaryLanguage + document.location.hash;
            }
        });
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
        App.Page.reopen({
            url: 'pages/' + language + '/pages'
        });

        this.setLocale(locale);
        this.initSelectViews();
    },

    injectUser: function (container, user) {
        // Set the currentUser model/content on the currentUser controller
        container.lookup('controller:currentUser').set('content', user);

        // Inject currentUser into all controllers
        container.typeInjection('controller', 'currentUser', 'controller:currentUser');
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

        App.Language.find().then(function(list) {
            App.LanguageSelectView.reopen({
                content: list
            });
        });

        App.ProjectPhase.find().then(function(data){

        App.ProjectPhaseSelectView.reopen({
            contentBinding: 'data',

            phases: function () {
                return App.ProjectPhase.find()
            }.property(),

            data: function () {
                return App.ProjectPhase.filter(function(item){
                    return item.get('viewable')})
                }.property('phases.length')
            });
        });

        App.ProjectPhaseChoiceView.reopen({
            sortProperties: ['sequence'],

            phases: function () {
                return App.ProjectPhase.find();
            }.property(),

            data: function () {
                return App.ProjectPhase.filter(function(item) {
                    return item.get('ownerEditable');
                });
            }.property('phases.length'),

            contentBinding: 'data'
        });
    },

    setLocale: function(locale) {
        if (!locale) {
            locale = this.get('locale');
        }

        if (locale != 'en-us') {
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
            if (locale == 'en-US') {
                Globalize.culture(locale);
            } else {
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

            }
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
        "bb_projects/manage": "bb_projects/manage",
        "bb_projects/plans/manage": "bb_projects/plans/manage",
        "bb_organizations/manage": "bb_organizations/manage",
        "bb_organizations/documents/manage": "bb_organizations/documents/manage",
        "bb_projects/budgetlines/manage": "bb_projects/budgetlines/manage",
        "users/activate": "users/activate",
        "users/passwordset": "users/passwordset",
        "users/time_available": "users/time_available",
        "homepage": "homepage",
        "contact/contact": "contact/contact",
        // TODO: Are the plurals below still needed?
        "bb_projects/wallposts/media": "bb_projects/wallposts/media",
        "bb_projects/wallposts/text": "bb_projects/wallposts/text",
        "bb_projects/campaigns/manage": "bb_projects/campaigns/manage",
        "bb_projects/pitches/manage": "bb_projects/pitches/manage",
        "bb_organizations/addresses/manage": "bb_organizations/addresses/manage",
        "bb_projects/ambassadors/manage": "bb_projects/ambassadors/manage",
    }
});

// Assigning plurals for model properties doesn't seem to work with extend, it does this way:
App.Adapter.configure("plurals", {
    "address": "addresses",
    "favourite_country" : "favourite_countries"
});

App.ApplicationController = Ember.Controller.extend({

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
    },

    // Override this to do something when the currentUser call in the initializer doesn't succeed
    missingCurrentUser: Em.K
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


DS.Model.reopen({
    meta_data: DS.attr('object')
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

//Enable Google Analytics with Ember
App.Router.reopen({
    /**
     * Tracks pageviews if google analytics is used
     * Source: http://www.randomshouting.com/2013/05/04/Ember-and-Google-Analytics.html
     *
     * TODO: With new Ember we can switch to a nicer pattern:
     * http://emberjs.com/guides/cookbook/helpers_and_components/adding_google_analytics_tracking/
     */
     didTransition: function(infos) {
        this._super(infos);

        /* 
        Clear queued (next) transition after any successful transition so the 
        queued one does not run more than once.
        */ 
        this.send('clearNextTransition');        

        Ember.run.next(function() {
            // the meta module will now go trough the routes and look for data
            App.meta.trigger('reloadDataFromRoutes');
        });

        var url = this.get('url');
        if (window._gaq !== undefined) {
            Ember.run.next(function() {
                _gaq.push(['_trackPageview', url]);
            });
        }
    }
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


App.ApplicationRoute = Em.Route.extend(BB.ModalMixin, {

    actions: {
        clearNextTransition: function () {
            this.set('nextTransition', null);
        },
        setNextTransition: function (transition) {
            this.set('nextTransition', transition);
        },
        loadNextTransition: function (fallbackRoute) {
            // If the applicationRoute has a nextTransition value then we run it as 
            // it is probably the case that the user tried to access a restricted page and 
            // was prevented from doing it => user was presented with the sign up / in modal.
            // If there is no nextTransition then load the passed route if defined.
            var nextTransition = this.get('nextTransition');
            if (nextTransition) {
                // retry the transition
                nextTransition.retry();

                // cancel the transition so that it doesn't run again
                this.send('clearNextTransition');
            } else if (Em.typeOf(fallbackRoute) == 'string') {
                this.transitionTo(fallbackRoute);
            }
        },
        setFlash: function (message, type) {
            var flash = {};
            flash.activeNameClass = 'is-active';

            if (typeof message === 'object') {
                flash = message;

            } else {
                flash.text = message;
                if (typeof type === 'undefined') {
                    flash.type = 'welcome'
                } else {
                    flash.type = type;
                }

            }
            this.controllerFor('application').set('flash', flash);
                setTimeout(function() {
                    $('.flash').removeClass('is-active');
                }, 3000);
        },
        logout: function () {
            // Do some logout stuff here!
        },
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

        showProjectTaskList: function(project_id) {
            var route = this;
            App.Project.find(project_id).then(function(project) {
                route.transitionTo('project', project);
                route.transitionTo('projectTaskList');
            });
        },

        showPage: function(pageId, newWindow) {
            if (Ember.typeOf(newWindow) == 'undefined')
                newWindow = false;

            var route = this;
            App.Page.find(pageId).then(function(page) {
                if (newWindow) {
                    var url = route.router.generate('page', page);
                    window.open(url, "_blank");
                } else {
                    route.transitionTo('page', page);
                    window.scrollTo(0, 0);
                }
            });
        }
    },

    urlForEvent: function(actionName, context) {
        return "/nice/stuff"
    }
});

// FIXME: we should make this cleaner by ensuring the current
//        user is fetched before we do any routing.
App.ErrorNotAllowedRoute = Em.Route.extend({
    beforeModel: function() {
        var self = this;
        App.CurrentUser.find('current').then( function (user) {
            if (user.get('isAuthenticated')) {
                self.transitionTo('home');
            }
        });
    }
});

App.UserIndexRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('userProfile');
    }
});
