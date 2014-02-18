from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.models import Site
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from .models import TaskMember


def send_mail_task_realized(task):
    """
    Send (multiple) e-mails when a task is realized.
    The task members that weren't rejected are the receivers.
    """
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
