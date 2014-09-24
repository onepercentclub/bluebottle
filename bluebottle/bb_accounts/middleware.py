"This is locale middleware on top of Django's default LocaleMiddleware."

from django.conf import settings
from django.middleware.locale import LocaleMiddleware as _LocaleMiddleware
from django.utils import translation
from django import http


class LocaleMiddleware(object):
    """
    If i18n_patterns are used, the language is not set in the session.
    This causes the middleware to potentially set an incorrect language on the
    current request when the frontend language differs from the browser language.

    This middleware fixes this in two ways:
        * first, a check is performed if the user is logged in. The preferred
          language is taken from his/her preferences.
        * If the user is logged in an a language is known: the language is set
          in the session, so future API calls pick the correct language.

        TODO: set the language in session for anonymous users.

        TODO: another workaround: when users (logged in or anonymous) select the
        language, is firing an API call which eventually calls Django's
        set_language view. This forces the language into the session.
    """

    def process_request(self, request):
        """ 
        This builds strongly on django's Locale middleware, so check 
        if it's enabled.

        This middleware is only relevant with i18n_patterns.
        """
        if self.enable_middleware():
            try:
                authenticated = request.user.is_authenticated()
            except AttributeError:
                authenticated = False

            if authenticated:
                lang_code = request.user.primary_language

                if lang_code:
                    # Early redirect based on language to prevent Ember from
                    # finding out and redirect after loading a complete page
                    # in the wrong language.
                    expected_url_lang_prefix = '/{0}/'.format(lang_code)
                    url_parts = request.path.split('/')

                    # Don't redirect on API requests
                    if url_parts[1] != 'api':
                        if len(url_parts) >= 2:
                            current_url_lang_prefix = url_parts[1]
                            if current_url_lang_prefix in dict(settings.LANGUAGES).keys() and not request.path.startswith(
                                    expected_url_lang_prefix):
                                new_location = request.get_full_path().replace(
                                    '/{0}/'.format(current_url_lang_prefix), expected_url_lang_prefix)

                                return http.HttpResponseRedirect(new_location)
                        # End early redirect.
                    
                    if translation.check_for_language(lang_code):
                        # activate the language
                        translation.activate(lang_code)
                        request.LANGUAGE_CODE = translation.get_language()

            else:
                if not request.LANGUAGE_CODE:
                    request.LANGUAGE_CODE = settings.LANGUAGE_CODE

    def process_response(self, request, response):
        """ Store the language """
        if self.enable_middleware():
            lang_code = translation.get_language()

            if hasattr(request, 'session'):
                """ Set the language in the session if it has changed """
                if (request.session.get('django_language', False) and 
                        request.session['django_language'] != lang_code):
                    request.session['django_language'] = lang_code
            else:
                """ Fall back to language cookie """
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
            
        # Headers, translation deactivation etc. is done in django's LocaleMiddleware
        return response

    def enable_middleware(self):
        if ('django.middleware.locale.LocaleMiddleware' in settings.MIDDLEWARE_CLASSES 
                and self.is_language_prefix_patterns_used()):
            return True
        return False

    # re-use the original function
    mw = _LocaleMiddleware()
    is_language_prefix_patterns_used = mw.is_language_prefix_patterns_used
