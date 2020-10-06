from builtins import object
import logging

from django.utils.translation import ugettext_lazy as _
from django_summernote.models import AbstractAttachment

logger = logging.getLogger(__name__)


class ProjectImage(AbstractAttachment):
    """
    Project Image: Image that is directly associated with the project.

    Can for example be used in project descriptions

    """

    class Meta(object):
        verbose_name = _('project image')
        verbose_name_plural = _('project images')
        permissions = (
            ('api_read_projectimage', 'Can view project imagesthrough the API'),
            ('api_add_projectimage', 'Can add project images through the API'),
            ('api_change_projectimage', 'Can change project images through the API'),
            ('api_delete_projectimage', 'Can delete project images through the API'),

            ('api_read_own_projectimage', 'Can view own project images through the API'),
            ('api_add_own_projectimage', 'Can add own project images through the API'),
            ('api_change_own_projectimage', 'Can change own project images through the API'),
            ('api_delete_own_projectimage', 'Can delete own project images through the API'),
        )

    def save(self, project_id=None, *args, **kwargs):
        if project_id:
            self.project_id = int(project_id[0])

        super(ProjectImage, self).save(*args, **kwargs)
