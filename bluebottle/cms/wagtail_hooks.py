from django.conf.urls import include, url
from django.core import urlresolvers

from wagtail.wagtailcore import hooks
from django.contrib.staticfiles.templatetags.staticfiles import static

from bluebottle.cms import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^cms/', include(admin_urls, namespace='cms', app_name='cms')),
    ]


@hooks.register('insert_editor_js')
def editor_js():
    return """
        <script src="{}"></script>
        <script>
            window.chooserUrls.projectChooser = '{}';
        </script>
    """.format(
        static('cms/js/project-chooser.js'), urlresolvers.reverse('cms:project_chooser')
    )
