from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.utils import translation
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.core.mail import EmailMultiAlternatives

from bluebottle.utils.utils import get_task_model, get_taskmember_model

TASK_MODEL = get_task_model()
TASK_MEMBER_MODEL = get_taskmember_model()


@receiver(post_save, weak=False, sender=TASK_MEMBER_MODEL)
def new_reaction_notification(sender, instance, created, **kwargs):
    task_member = instance
    task = instance.task

    site = 'https://' + Site.objects.get_current().domain

    # Project Wall Post
    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.applied:
        receiver = task.author
        sender = task_member.member
        link = '/en/#!/tasks/{0}'.format(task.id)

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

    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.rejected:
        sender = task.author
        receiver = task_member.member
        task_list = '/en/#!/tasks'
        link = '/en/#!/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s found someone else to do the task you applied for.') % {'sender': sender.get_short_name()}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
                           'task_list': task_list})
        text_content = get_template('task_member_rejected.mail.txt').render(context)
        html_content = get_template('task_member_rejected.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.accepted:
        sender = task.author
        receiver = task_member.member
        link = '/en/#!/tasks/{0}'.format(task.id)

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

    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.realized:
        sender = task.author
        receiver = task_member.member
        link = '/en/#!/tasks/{0}'.format(task.id)
        task_list = '/en/#!/tasks'
        project_link = '/en/#!/projects/{0}'.format(task.project.slug)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('You realised your Booking Cares task!')
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
                           'task_list':task_list, 'project_link':project_link})
        text_content = get_template('task_member_realized.mail.txt').render(context)
        html_content = get_template('task_member_realized.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@receiver(pre_delete, weak=False, sender=TASK_MEMBER_MODEL)
def task_member_withdraw(sender, instance, **kwargs):
    task_member = instance
    task = instance.task

    site = 'https://' + Site.objects.get_current().domain

    receiver = task.author
    sender = task_member.member
    link = '/en/#!/tasks/{0}'.format(task.id)
    task_list = '/en/#!/tasks'
    project_link = '/en/#!/projects/{0}'.format(task.project.slug)

    # Compose the mail
    # Set the language for the receiver
    translation.activate(receiver.primary_language)
    subject = _('{name} is no longer available for the task').format(name=task_member.member.get_short_name())
    context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
                       'task_list':task_list, 'project_link':project_link})
    text_content = get_template('task_member_withdrew.mail.txt').render(context)
    html_content = get_template('task_member_withdrew.mail.html').render(context)
    translation.deactivate()
    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()




# @receiver(post_save, weak=False, sender=TASK_MODEL)
# def send_mail_task_realized(sender, instance, created, **kwargs):
#     """
#     Send (multiple) e-mails when a task is realized.
#     The task members that weren't rejected are the receivers.
#     """
#
#     if not created and instance.status == 'realized':
#         task = instance
#         sender = task.author
#         link = '/go/tasks/{0}'.format(task.id)
#         site = 'https://' + Site.objects.get_current().domain
#
#         qs = task.members.all().exclude(status=TASK_MEMBER_MODEL.TaskMemberStatuses.rejected).select_related('member')
#         receivers= [taskmember.member for taskmember in qs]
#         emails = []
#
#         for receiver in receivers:
#             translation.activate(receiver.primary_language)
#             subject = _('Good job! "%(task)s" is realized!.') % {'task': task.title}
#             context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
#             text_content = get_template('task_realized.mail.txt').render(context)
#             html_content = get_template('task_realized.mail.html').render(context)
#             translation.deactivate()
#             msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
#             msg.attach_alternative(html_content, "text/html")
#             emails.append(msg)
#
#         if emails:
#             connection = get_connection()
#             connection.send_messages(emails)
#             connection.close()

