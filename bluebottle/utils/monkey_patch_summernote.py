from django_summernote.utils import SUMMERNOTE_THEME_FILES

SUMMERNOTE_THEME_FILES['bs3'] = {
    'base_css': (
        '/static/assets/summernote/bootstrap.min.css',
    ),
    'base_js': (
        '/static/assets/admin/js/vendor/jquery/jquery.min.js',
        '/static/assets/summernote/bootstrap.min.js'
    ),
    'default_css': (
        'summernote/summernote.min.css',
        'summernote/django_summernote.css',
    ),
    'default_js': (
        'summernote/jquery.ui.widget.js',
        'summernote/jquery.iframe-transport.js',
        'summernote/jquery.fileupload.js',
        'summernote/summernote.min.js',
        'summernote/ResizeSensor.js',
    ),
}
