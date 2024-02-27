require('es6-promise').polyfill();

var gulp = require('gulp'),
    browserify = require('browserify'),
    concatCss = require('gulp-concat-css'),
    cleanCSS = require('gulp-clean-css'),
    sass = require('gulp-sass')(require('node-sass')),
    uglify = require('gulp-uglify'),
    buffer = require('vinyl-buffer'),
    source = require('vinyl-source-stream'),
    sourcemaps = require('gulp-sourcemaps'),
    merge = require('merge-stream'),
    postcss = require('gulp-postcss'),
    pxtorem = require('postcss-pxtorem'),
    autoprefixer = require('autoprefixer'),
    shell = require('gulp-shell'),
    replace = require('gulp-replace');

var cssProcessors = [
    autoprefixer(),
    pxtorem({
        rootValue: 14,
        replace: false,
        propWhiteList: []
    })
];

gulp.task('scripts', function() {
    return browserify('./js/src/main.js')
        .bundle()
        .on('error', function(error) {
            console.error(error);
        })
        .pipe(source('bundle.min.js'))
        .pipe(buffer())
        .pipe(uglify())
        .pipe(gulp.dest('./js/build/'));
});

gulp.task('styles', function() {
    return gulp.src('./css/**/*.scss')
        .pipe(sourcemaps.init())
        .pipe(sass({
            outputStyle: 'compressed'
        }))
        .on('error', function(error) {
            console.error(error);
        })
        .pipe(postcss(cssProcessors))
        .on('error', function(error) {
            console.error(error);
        })
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('./css'));
});

gulp.task('vendor-styles', function() {
    return merge(
        gulp.src('./node_modules/jquery-ui/themes/base/images/*')
            .pipe(gulp.dest('./css/jquery-ui/images/')),
        merge(
            gulp.src([
                './node_modules/select2/dist/css/select2.css',
            ]),
            gulp.src([
                './node_modules/jquery-ui/themes/base/all.css'
            ]).pipe(cleanCSS()) // needed to remove jQuery UI comments breaking concatCss
                .on('error', function(error) {
                    console.error(error);
                })
                .pipe(concatCss('jquery-ui.css', {
                    rebaseUrls: false
                }))
                .on('error', function(error) {
                    console.error(error);
                })
                .pipe(replace('images/', 'jquery-ui/images/'))
                .on('error', function(error) {
                    console.error(error);
                }),
        ).pipe(postcss(cssProcessors))
            .on('error', function(error) {
                console.error(error);
            })
            .pipe(concatCss('vendor.css', {
                rebaseUrls: false
            }))
            .on('error', function(error) {
                console.error(error);
            })
            .pipe(cleanCSS())
            .on('error', function(error) {
                console.error(error);
            })
            .pipe(gulp.dest('./css'))
    )
});

gulp.task('vendor-translations', function() {
    return merge(
        gulp.src(['./node_modules/jquery-ui/ui/i18n/*.js'])
            .pipe(gulp.dest('./js/i18n/jquery-ui/')),
        gulp.src(['./node_modules/timepicker/i18n/*.js'])
            .pipe(gulp.dest('./js/i18n/jquery-ui-timepicker/')),
        gulp.src(['./node_modules/select2/dist/js/i18n/*.js'])
            .pipe(gulp.dest('./js/i18n/select2/'))
    )
});

gulp.task('build', gulp.parallel('scripts', 'styles', 'vendor-styles', 'vendor-translations'));

gulp.task('watch', function() {
    gulp.watch('./js/src/**/*.js', gulp.series('scripts'));
    gulp.watch('./css/**/*.scss', gulp.series('styles'));
});

gulp.task('default', gulp.parallel('build', 'watch'));
