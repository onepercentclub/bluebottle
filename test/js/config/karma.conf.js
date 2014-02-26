// Karma configuration
// Generated on Tue Oct 29 2013 16:49:15 GMT+0100 (CET)

module.exports = function(config) {
  config.set({

    // base path, that will be used to resolve files and exclude
    basePath: '../',

    plugins: [
      'karma-qunit',
      'karma-chrome-launcher',
      'karma-coverage',
      'karma-ember-preprocessor',
      'karma-phantomjs-launcher'
    ],

    preprocessors: {
      // '../../apps/**/templates/*.hbs': 'ember',
      '../../apps/**/static/**/*.js': ['coverage']
    },

    // frameworks to use
    frameworks: ['qunit'],

    // list of files / patterns to load in the browser
    files: [
      // Ember ENV for Testing
      'config/test_env.js',

      // Vendor - concat using grunt
      '../../static/build/js/lib/deps.js',

      // Load ember configs for testing env
      'config/ember_config.js',

      { pattern: '/static/assets/js/vendor/globalize-cultures/globalize.culture.*.js', included: false, served: false },

      // Bluebottle / 1%Club Site Static
      '../../bluebottle/common/static/js/bluebottle/app.js',
      '../../bluebottle/common/static/js/bluebottle/presets.js', 
      '../../bluebottle/common/static/js/bluebottle/utils.js', 

      // Stubs for Bluebottle API
      'config/test_stubs.js',

      // 1%Club Site App
      '../../bluebottle/**/static/js/bluebottle/**/{components,controllers,models,routes,views}.js',

      // Handlebar Templates
      // Need to do some preprocessing first to get the django processed
      // Handlebars templates before loading them here!
      // '../../apps/**/templates/*.hbs',

      // Test Libs - concat using grunt
      '../../static/build/js/lib/test_deps.js',

      // Load sinon configs for testing env
      'config/sinon_config.js',

      // Factories / Fixtures
      'factories/**/*_factory.js',
      'fixtures/*.js',

      // Test Config and Helpers
      'config/test_config.js',
      'helpers/*_helpers.js',

      // Unit Tests
      'unit/**/helpers.js',
      'unit/**/*_test.js',

      // Integration Tests
      'integration/**/helpers.js',
      'integration/**/*_test.js'
    ],

    // list of files to exclude
    exclude: [
      
    ],

    // test results reporter to use
    // possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
    reporters: ['progress', 'coverage', 'growl'],

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_ERROR,

    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,

    // Start these browsers, currently available:
    // - Chrome
    // - ChromeCanary
    // - Firefox
    // - Opera (has to be installed with `npm install karma-opera-launcher`)
    // - Safari (only Mac; has to be installed with `npm install karma-safari-launcher`)
    // - PhantomJS
    // - IE (only Windows; has to be installed with `npm install karma-ie-launcher`)
    browsers: ['PhantomJS'],

    // If browser does not capture in given timeout [ms], kill it
    captureTimeout: 60000,

    // Continuous Integration mode
    // if true, it capture browsers, run tests and exit
    singleRun: false
  });
};
