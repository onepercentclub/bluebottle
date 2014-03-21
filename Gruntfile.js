module.exports = function (grunt) {
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-ember-template-compiler');
  grunt.loadNpmTasks('grunt-hashres');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-bower-task'); 
  grunt.loadNpmTasks('grunt-contrib-uglify'); 
  grunt.loadNpmTasks('grunt-microlib');
  grunt.loadNpmTasks('grunt-shell');

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
    watch: {
      scripts: {
        files: ['apps/static/script/**/*.js', 'ember/static/script/templates/*.handlebars'],
        tasks: ['dev'],
        options: {
          interrupt: true,
          debounceDelay: 250
        }
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
          'static/build/js/components/jquery-mockjax/jquery.mockjax.js',
          'static/build/js/components/pavlov/pavlov.js',
          'bluebottle/common/static/js/vendor/handlebars-1.0.0.js',
          'bluebottle/common/static/js/vendor/ember-v1.0.0.js',
          'bluebottle/common/static/js/vendor/ember-data-v0.14.js',
          'bluebottle/common/static/js/vendor/ember-data-drf2-adapter.js',
          'bluebottle/common/static/js/vendor/ember-meta.js',
          'bluebottle/common/static/js/plugins/ember.hashbang.js',
          'bluebottle/common/static/js/vendor/globalize.js',
          'bluebottle/common/static/jsi18n/en-us/*.js',
        ],
        dest: 'static/build/js/lib/deps.js'
      },
      test: {
        src: [
          'static/build/js/components/jquery-mockjax/jquery.mockjax.js',
          'static/build/js/components/pavlov/pavlov.js',
          'static/build/js/components/ember-data-factory/dist/ember-data-factory-0.0.1.js',
          // Sion
          'static/build/js/components/sinon/lib/sinon.js',
          'static/build/js/components/sinon/lib/sinon/match.js',
          'static/build/js/components/sinon/lib/sinon/spy.js',
          'static/build/js/components/sinon/lib/sinon/call.js',
          'static/build/js/components/sinon/lib/sinon/behavior.js',
          'static/build/js/components/sinon/lib/sinon/stub.js',
          'static/build/js/components/sinon/lib/sinon/mock.js',
          'static/build/js/components/sinon/lib/sinon/assert.js',
          'static/build/js/components/sinon/lib/sinon/util/event.js',
          'static/build/js/components/sinon/lib/sinon/util/fake_xml_http_request.js',
          'static/build/js/components/sinon/lib/sinon/util/fake_timers.js',
          'static/build/js/components/sinon/lib/sinon/util/fake_server.js',
          'static/build/js/components/sinon/lib/sinon/util/fake_server_with_clock.js',
          'static/build/js/components/sinon/lib/sinon/collection.js',
          'static/build/js/components/sinon/lib/sinon/sandbox.js',
          'static/build/js/components/sinon/lib/sinon/test.js',
          'static/build/js/components/sinon/lib/sinon/test_case.js',
          // 'static/build/js/components/sinon-qunit/lib/sinon-qunit.js'
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
    }
  });

  grunt.registerTask('default', ['dev']);
  grunt.registerTask('build', ['bower:install', 'concat:dist', 'concat:test']);
  // Add 'shell:parse_templates' and 'emberhandlebars' tasks to dev once it is working
  grunt.registerTask('dev', ['build', 'karma:unit']);
  grunt.registerTask('travis', ['build', 'karma:ci']);
  grunt.registerTask('local', ['dev', 'watch']);
  grunt.registerTask('deploy', ['concat:dist', 'uglify:dist', 'hashres']);
}
