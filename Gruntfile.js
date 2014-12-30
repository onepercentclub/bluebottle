module.exports = function (grunt) {
  require('time-grunt')(grunt);
  require('jit-grunt')(grunt);

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-ember-template-compiler');
  grunt.loadNpmTasks('grunt-hashres');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-concurrent');
  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-bower-task'); 
  grunt.loadNpmTasks('grunt-contrib-uglify'); 
  grunt.loadNpmTasks('grunt-microlib');
  grunt.loadNpmTasks('grunt-shell');
  grunt.loadNpmTasks('grunt-contrib-compass');

  var sassOutputStyle = grunt.option('output_style') || 'expanded',
    staticPath = './bluebottle/common/static/',
    compassPath = staticPath + 'sass',
    sassPath = staticPath + 'refactor-sass',
    cssOutputPath = staticPath + '/css';

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    karma: {
        ci: { configFile: 'test/js/config/karma.conf.js', singleRun: true, browsers: ['PhantomJS'] },
      unit: { configFile: 'test/js/config/karma.conf.js', keepalive: true, browsers: ['Chrome'] },
      unitSpec: { configFile: 'test/js/config/karma.conf.js', keepalive: true, browsers: ['Chrome'], reporters: ['spec'] },
      chrome: { configFile: 'test/js/config/karma.conf.js', keepalive: true, browsers: ['Chrome'] }
      // e2e: { configFile: 'test/js/config/e2e.js', keepalive: true }, // End-to-end / Functional Tests
      // watch: { configFile: 'test/js/config/unit.js', singleRun:false, autoWatch: true, keepalive: true }
    },
    shell: {
      parse_templates: {
        options: {
          failOnError: true
        },
        command: 'rm -f ./static/build/js/templates/**/*.handlebars ; python ./parse_templates.py -d ./static/build/js/templates'
      }
    },
    concurrent: {
        dev: {
            tasks: ['watch:ember', 'karma:unit'],
            options: {
                logConcurrentOutput: true
            }
        }
    },
    watch: {
      ember: {
        files: ['Gruntfile.js', 'test/js/config/*.js', 'bluebottle/**/static/js/**/*.js', 'bluebottle/**/templates/**/*.hbs'],
        tasks: ['build'],
        options: {
          interrupt: true,
          debounceDelay: 250,
          atBegin: true
        }
      },
      scss: {
        files: ['bluebottle/common/static/**/*'],
        tasks: ['compass:dev'],
      }      
    },
    hashres: {
      options: {
        renameFiles: true
      },
      prod: {
        src: ['static/build/js/lib/deps.min.js'],
        dest: 'ember/person/templates/index.html'
      }
    },
    bower: {
      install: {
        options: {
          targetDir: 'static/build/js/components',
          cleanTargetDir: true,
          cleanBowerDir: true,
          install: true,
          copy: true
        }
      },
      cleanup: {
        options: {
          targetDir: 'static/build/js/components',
          cleanTargetDir: true,
          cleanBowerDir: true,
          install: false,
          copy: false
        }
      }
    },
    concat: {
      dist: {
        src: [
          'bluebottle/common/static/js/vendor/jquery-1.8.3.js',
          'node_modules/jquery-mockjax/jquery.mockjax.js',

          // Vendor
          'bluebottle/common/static/js/vendor/handlebars-1.0.0.js',
          'bluebottle/common/static/js/vendor/ember-v1.0.0.js',
          'bluebottle/common/static/js/vendor/ember-data-v0.14.js',
          'bluebottle/common/static/js/vendor/ember-data-drf2-adapter.js',
          'bluebottle/common/static/js/vendor/ember-meta.js',
          'bluebottle/common/static/js/vendor/globalize.js',
          'bluebottle/common/static/jsi18n/en-us/*.js',

          // Plugins
          'bluebottle/common/static/js/plugins/ember-facebook.js',
          'bluebottle/common/static/js/plugins/ember.hashbang.js',
          'bluebottle/common/static/js/plugins/bb_modal.js',
          'bluebottle/common/static/js/plugins/apiary-adapter.js'
        ],
        dest: 'static/build/js/lib/deps.js'
      },
      test: {
        src: [
          'node_modules/qunitjs/qunit/qunit.js',
          'static/build/js/components/pavlov/pavlov.js',
          'static/build/js/components/ember-data-factory/dist/ember-data-factory-0.0.1.js',
          // Sion
          'node_modules/sinon/lib/sinon.js',
          'node_modules/sinon/lib/sinon/match.js',
          'node_modules/sinon/lib/sinon/spy.js',
          'node_modules/sinon/lib/sinon/call.js',
          'node_modules/sinon/lib/sinon/behavior.js',
          'node_modules/sinon/lib/sinon/stub.js',
          'node_modules/sinon/lib/sinon/mock.js',
          'node_modules/sinon/lib/sinon/assert.js',
          'node_modules/sinon/lib/sinon/util/event.js',
          'node_modules/sinon/lib/sinon/util/fake_xml_http_request.js',
          'node_modules/sinon/lib/sinon/util/fake_timers.js',
          'node_modules/sinon/lib/sinon/util/fake_server.js',
          'node_modules/sinon/lib/sinon/util/fake_server_with_clock.js',
          'node_modules/sinon/lib/sinon/collection.js',
          'node_modules/sinon/lib/sinon/sandbox.js',
          'node_modules/sinon/lib/sinon/test.js',
          'node_modules/sinon/lib/sinon/test_case.js',
          // 'node_modules/sinon-qunit/lib/sinon-qunit.js'
        ],
        dest: 'static/build/js/lib/test_deps.js'
      },
    },
    uglify: {
      options: {
        // the banner is inserted at the top of the output
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          '<%= pkg.name %>.min.js': ['<%= concat.dist.dest %>']
        }
      }
    },
    emberhandlebars: {
      compile: {
        options: {
          templateName: function(sourceFile) {
            return sourceFile.match(/\/([0-9|a-z|\.|_]+)\.handlebars/i)[1];
          }
        },
        files: ['static/build/js/templates/*.handlebars'],
        dest: 'static/build/js/templates.js'
      }
    },
    sass: {
      dist: {
        files: [{
          expand: true,
          cwd: sassPath,
          src: 'screen-refactor.scss',
          dest: cssOutputPath,
          ext: '.css'
        }]
      }
    },
    compass: {
      // live
      dist: {
        options: {
          httpPath: '/static/assets/',
          basePath: staticPath,
          sassDir: 'sass',
          cssDir: 'css',
          imagesDir: 'images',          
          javascriptsDir: 'js',          
          outputStyle: sassOutputStyle,
          relativeAssets: true,
          noLineComments: true,
          environment: 'production',
          raw: 'preferred_syntax = :scss\n', // Use `raw` since it's not directly available
          importPath: compassPath,
          force: true
        }
      },
      // development
      dev: {
        options: {
          httpPath: '/static/assets/',
          basePath: staticPath,
          sassDir: 'sass',
          cssDir: 'css',
          imagesDir: 'images',          
          javascriptsDir: 'js',          
          outputStyle: sassOutputStyle,
          relativeAssets: true,
          noLineComments: false,
          raw: 'preferred_syntax = :scss\n', // Use `raw` since it's not directly available  
          importPath: compassPath,
          force: false, 
          sourcemap: true
        }
      }
    }
  });

  grunt.registerTask('default', ['concurrent:dev']);
  grunt.registerTask('build', ['bower:install', 'concat:dist', 'concat:test', 'shell:parse_templates']);
  grunt.registerTask('dev', ['build', 'karma:unit']);
  grunt.registerTask('travis', ['build', 'karma:ci']);
  grunt.registerTask('local', ['dev', 'watch']);
  grunt.registerTask('deploy', ['concat:dist', 'uglify:dist', 'hashres', 'compass:dist']);
  grunt.registerTask('build:css', ['sass:dist', 'compass:dist']);
};