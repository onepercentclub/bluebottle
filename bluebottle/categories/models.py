from django.db import models
from django.utils.translation import ugettext as _
from bluebottle.utils.fields import ImageField


class Category(models.Model):
    """
        Some projects are run in cooperation with a partner
        organization like EarthCharter & MacroMicro
    """
    title = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"))
    image = ImageField(_("image"), max_length=255, blank=True, null=True,
                       upload_to='categories/',
                       help_text=_("Category image"))

    @property
    def projects(self):
        return self.project_set.order_by('-favorite', '-popularity').filter(
            status__slug__in=['campaign', 'done-complete', 'done-incomplete',
                              'voting', 'voting-done'])

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __unicode__(self):
        return self.title
