from django.utils.translation import ugettext_lazy as _

from bluebottle.bb_tasks.models import BaseTask
from bluebottle.wallposts.notifiers import (WallpostObserver, ReactionObserver,
                                            ObserversContainer)
from bluebottle.mail import send_mail


class TaskWallObserver(WallpostObserver):

    model = BaseTask

    def __init__(self, instance):
        WallpostObserver.__init__(self, instance)

    def notify(self):
        task = self.post
        task_owner = task.author

        # no check if the author is the same of the sender. Look at
        # ProjectWallNotificator
        send_mail(
            template_name='task_wallpost_new.mail',
            subject=_('%(author)s commented on your task') % {'author': self.author.get_short_name()},
            to=task_owner,

            task=task,
            link='/go/tasks/{0}'.format(task.id),
            site=self.site,
            author=self.author,
            receiver=task_owner
        )


class TaskReactionObserver(ReactionObserver):

    model = BaseTask

    def __init__(self, instance):
        ReactionObserver.__init__(self, instance)

    def notify(self):
        task = self.post.content_object
        task_author = task.author

        # Make sure users only get mailed once!
        mailed_users = set()

        # It's commented out... check why

        # # Implement 2c: send email to other Reaction authors that are not
        # the Object owner or the post author.
        # reactions = post.reactions.exclude(
        #   Q(author=post_author) |
        #   Q(author=project_owner) |
        #   Q(author=reaction_author))
        # for r in reactions:
        #     if r.author not in mailed_users:
        #         send_mail(
        #             template_name='project_wallpost_reaction_same_wallpost.mail',
        #             subject=_('%(author)s replied on your comment') % {'author': reaction_author.first_name},
        #             to=r.author,
        #
        #             project=project,
        #             link='/go/projects/{0}'.format(project.slug),
        #             author=reaction_author
        #         )
        #         mailed_users.add(r.author)

        # # Implement 2b: send email to post author, if Reaction author is not
        # the post author.
        if self.reaction_author != self.post_author:
            if self.reaction_author not in mailed_users and self.post_author:
                send_mail(
                    template_name='task_wallpost_reaction_new.mail',
                    subject=_('%(author)s replied on your comment') % {'author': self.reaction_author.get_short_name()},
                    to=self.post_author,
                    site=self.site,
                    task=task,
                    link='/go/tasks/{0}'.format(task.id),
                    author=self.reaction_author,
                    receiver=self.post_author
                )
                mailed_users.add(self.post_author)

        # Implement 2a: send email to Object owner, if Reaction author is not
        # the Object owner.
        if self.reaction_author != task_author:
            if task_author not in mailed_users:
                send_mail(
                    template_name='task_wallpost_reaction_task.mail',
                    subject=_('%(author)s commented on your task') % {'author': self.reaction_author.get_short_name()},
                    to=task_author,

                    site=self.site,
                    task=task,
                    link='/go/tasks/{0}'.format(task.id),
                    author=self.reaction_author,
                    receiver=task_author
                )

ObserversContainer().register(TaskWallObserver)
ObserversContainer().register(TaskReactionObserver)
