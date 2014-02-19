from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.contrib.sites.models import Site
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from .models import TaskMember, BaseTask


@receiver(post_save, weak=False, sender=TaskMember)
def new_reaction_notification(sender, instance, created, **kwargs):
    task_member = instance
    # task = BaseTask.members
    task = instance.task

    site = 'https://' + Site.objects.get_current().domain

    # Project Wall Post
    if task_member.status == TaskMember.TaskMemberStatuses.applied:
        receiver = task.author
        sender = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s applied for your task.') % {'sender': sender.get_short_name()}
        ctx = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
                       'motivation': task_member.motivation})
        text_content = render_to_string('task_member_applied.mail.txt', context_instance=ctx)
        html_content = render_to_string('task_member_applied.mail.html', context_instance=ctx)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    if task_member.status == TaskMember.TaskMemberStatuses.rejected:
        sender = task.author
        receiver = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s found someone else to do the task you applied for.') % {'sender': sender.get_short_name()}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_member_rejected.mail.txt').render(context)
        html_content = get_template('task_member_rejected.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    if task_member.status == TaskMember.TaskMemberStatuses.accepted:
        sender = task.author
        receiver = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s accepted you to complete the tasks you applied for.') % {'sender': sender.get_short_name()}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_member_accepted.mail.txt').render(context)
        html_content = get_template('task_member_accepted.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


def send_mail_task_realized(task):
    """ Send (multiple) e-mails when a task is realized. The task members that weren't rejected are the receivers. """
    sender = task.author
    link = '/go/tasks/{0}'.format(task.id)
    site = 'https://' + Site.objects.get_current().domain

    qs = task.taskmember_set.exclude(status=TaskMember.TaskMemberStatuses.rejected).select_related('member')
    receivers = [taskmember.member for taskmember in qs]

    emails = []

    for receiver in receivers:
        translation.activate(receiver.primary_language)
        subject = _('Good job! "%(task)s" is realized!.') % {'task': task.title}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_realized.mail.txt').render(context)
        html_content = get_template('task_realized.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        emails.append(msg)

    connection = get_connection()
    connection.send_messages(emails)
    connection.close()
