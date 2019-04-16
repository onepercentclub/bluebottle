from bluebottle.notifications.messages import TransitionMessage


class InitiativeApproveOwnerMessage(TransitionMessage):
    subject = 'Your initiative has been approved'
    template = 'messages/initiative_approved_owner'
