from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from tenant_extras.utils import TenantLanguage

from bluebottle.bb_projects.models import BaseProject
from bluebottle.wallposts.notifiers import (
    WallpostObserver, ReactionObserver, ObserversContainer
)
from bluebottle.utils.email_backend import send_mail


class ProjectWallObserver(WallpostObserver):

    model = BaseProject

    def __init__(self, instance):
        WallpostObserver.__init__(self, instance)

    def notify(self):
        project = self.parent

        for manager in set([project.owner, project.task_manager, project.promoter]):

            # Implement 1a: send email to Object owner, if Wallpost author is not
            # the Object owner.
            if manager and self.author != manager:

                with TenantLanguage(manager.primary_language):
                    subject = _('%(author)s commented on your project') % {
                        'author': self.author.get_short_name()}

                send_mail(
                    template_name='project_wallpost_new.mail',
                    subject=subject,
                    to=manager,
                    project=project,
                    link='/go/projects/{0}'.format(project.slug),
                    author=self.author,
                    receiver=manager
                )


class ProjectReactionObserver(ReactionObserver):

    model = BaseProject

    def __init__(self, instance):
        ReactionObserver.__init__(self, instance)

    def notify(self):
        project = self.post.content_object

        # Make sure users only get mailed once!
        mailed_users = set()

        # Implement 2c: send email to other Reaction authors that are not the
        # Object owner or the post author.
        reactions = self.post.reactions.exclude(Q(author=self.post_author) |
                                                Q(author=project.owner) |
                                                Q(author=self.reaction_author))
        for r in reactions:
            if r.author not in mailed_users:
                with TenantLanguage(r.author.primary_language):
                    subject = _('%(author)s replied on your comment') % {
                        'author': self.reaction_author.get_short_name()}

                send_mail(
                    template_name='project_wallpost_reaction_same_wallpost.mail',
                    subject=subject,
                    to=r.author,
                    project=project,
                    link='/go/projects/{0}'.format(project.slug),
                    author=self.reaction_author,
                    receiver=r.author
                )
                mailed_users.add(r.author)

        # Implement 2b: send email to post author, if Reaction author is not
        # the post author.
        if self.reaction_author != self.post_author:
            if self.reaction_author not in mailed_users and self.post_author:

                with TenantLanguage(self.post_author.primary_language):
                    subject = _('%(author)s replied on your comment') % {
                        'author': self.reaction_author.get_short_name()}

                send_mail(
                    template_name='project_wallpost_reaction_new.mail',
                    subject=subject,
                    to=self.post_author,
                    project=project,
                    link='/go/projects/{0}'.format(project.slug),
                    site=self.site,
                    author=self.reaction_author,
                    receiver=self.post_author
                )
                mailed_users.add(self.post_author)

        # Implement 2a: send email to Object owner, if Reaction author is not
        # the Object owner.
        for manager in set([project.owner, project.task_manager, project.promoter]):

            if manager and self.reaction_author != manager:
                if manager not in mailed_users:

                    with TenantLanguage(manager.primary_language):
                        subject = _('%(author)s commented on your project') % {
                            'author': self.reaction_author.get_short_name()}

                    send_mail(
                        template_name='project_wallpost_reaction_project.mail',
                        subject=subject,
                        to=manager,
                        project=project,
                        site=self.site,
                        link='/go/projects/{0}'.format(project.slug),
                        author=self.reaction_author,
                        receiver=manager
                    )


ObserversContainer().register(ProjectWallObserver)
ObserversContainer().register(ProjectReactionObserver)
