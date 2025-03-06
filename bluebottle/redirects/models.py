from builtins import object
from django.db import models
from django.utils.translation import gettext_lazy as _


class Redirect(models.Model):
    old_path = models.CharField(
        _('redirect from'), max_length=200, db_index=True, unique=True,
        help_text=_(
            "This should be an absolute path, excluding the "
            "domain name. Example: '/events/search/'."
        )
    )

    new_path = models.CharField(
        _('redirect to'),
        max_length=200,
        blank=True,
        help_text=_(
            "This can be either an absolute path (as above) "
            "or a full URL starting with 'http://'."
        )
    )

    regular_expression = models.BooleanField(
        _('Match using regular expressions'),
        default=False,
        help_text=_(
            "If checked, the redirect-from and redirect-to fields "
            "will also be processed using regular expressions when "
            "matching incoming requests.<br>Example: "
            "<strong>/projects/.* -> /#!/projects</strong> will "
            "redirect everyone visiting a page starting with "
            "/projects/<br>Example: <strong>/projects/(.*) -> "
            "/#!/projects/$1</strong> will turn /projects/myproject "
            "into /#!/projects/myproject<br><br>Invalid regular "
            "expressions will be ignored."
        )
    )

    class Meta(object):
        verbose_name = _('redirect')
        verbose_name_plural = _('redirects')
        db_table = 'django_redirect'
        ordering = ('old_path',)

    def __str__(self):
        return f"{self.old_path} => {self.new_path}"
