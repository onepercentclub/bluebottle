from bluebottle.notifications.messages import TransitionMessage


class InitiativeApproveOwnerMessage(TransitionMessage):
    subject = 'Your initiative has been approved'
    template = 'messages/initiative_approved_owner'


class InitiativeNeedsWorkOwnerMessage(TransitionMessage):
    subject = 'Your initiative needs work'
    template = 'messages/initiative_needs_work_owner'


class InitiativeClosedOwnerMessage(TransitionMessage):
    subject = 'Your initiative has been closed'
    template = 'messages/initiative_closed_owner'
