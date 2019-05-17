class TransitionMessage(object):
    def __init__(self, instance):
        self.instance = instance

    def send(self):
        print 'sending message to {}, with the subject {}'.format(
            getattr(self.instance, self.recipient),
            self.subject
        )


class SubmitMessage(TransitionMessage):
    recipient = 'owner'
    subject = 'Your initiative was submitted'
    template = 'utils/messages/submitted'
