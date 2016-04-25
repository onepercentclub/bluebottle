COMPRESS_ENABLED = True
COMPRESS_TEMPLATES = True

TEMPLATE_LOADERS = (
    ('tenant_extras.template_loaders.CachedLoader', (
        'tenant_extras.template_loaders.FilesystemLoader',
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader'
    )),
)

COMPRESS_PRECOMPILERS = (
    ('text/x-handlebars', 'embercompressorcompiler.filter.EmberHandlebarsCompiler'),
)

CACHES = {
    'default': {
        'BACKEND': 'tenant_extras.cache.TenantAwareMemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
