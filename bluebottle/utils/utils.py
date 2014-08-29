from django_fsm.db.fields import TransitionNotAllowed
import logging

class StatusDefinition:
    """
    Various status definitions for FSM's
    """
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    CREATED = 'created'
    LOCKED = 'locked'
    SUCCESS = 'success'
    STARTED = 'started'
    CANCELLED = 'cancelled'
    AUTHORIZED = 'authorized'
    SETTLED = 'settled'
    CHARGED_BACK = 'charged_back'
    REFUNDED = 'refunded'
    PAID = 'paid'
    FAILED = 'failed'
    UNKNOWN = 'unknown'

class FSMTransition:

    """
    Class mixin to add transition_to method for Django FSM
    """
    def transition_to(self, new_status):
        # If the new_status is the same as then current then return early
        if self.status == new_status:
            return

        # Lookup the available next transition - from Django FSM
        available_transitions = self.get_available_status_transitions()

        logging.debug("{0} state change: '{1}' to '{2}'".format(self.__class__.__name__, self.status, new_status))

        # Check that the new_status is in the available transitions - created with Django FSM decorator
        try:
            transition_method = [i[1] for i in available_transitions if i[0] == new_status].pop()
        except IndexError:
            # TODO: should we raise exception here?
            raise TransitionNotAllowed(
                "Can't switch from state '{0}' to state '{1}' for {2}".format(self.status, new_status, self.__class__.__name__))
         
        # Get the function method on the instance 
        instance_method = getattr(self, transition_method.__name__)

        # Call state transition method
        try:
            instance_method()
        except Exception as e:
            raise e


def get_client_ip(request):
    """ A utility method that returns the client IP for the given request. """

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def set_author_editor_ip(request, obj):
    """ A utility method to set the author, editor and IP address on an object based on information in a request. """

    if not hasattr(obj, 'author'):
        obj.author = request.user
    else:
        obj.editor = request.user
    obj.ip_address = get_client_ip(request)


def clean_for_hashtag(text):
    """
    Strip non alphanumeric charachters.

    Sometimes, text bits are made up of two parts, sepated by a slash. Split
    those into two tags. Otherwise, join the parts separated by a space.
    """
    tags = []
    bits = text.split('/')
    for bit in bits:
        # keep the alphanumeric bits and capitalize the first letter
        _bits = [_bit.title() for _bit in bit.split() if _bit.isalnum()]
        tag = "".join(_bits)
        tags.append(tag)

    return " #".join(tags)


def clean_for_hashtag(text):
    """
    Strip non alphanumeric charachters.

    Sometimes, text bits are made up of two parts, sepated by a slash. Split
    those into two tags. Otherwise, join the parts separated by a space.
    """
    tags = []
    bits = text.split('/')
    for bit in bits:
        # keep the alphanumeric bits and capitalize the first letter
        _bits = [_bit.title() for _bit in bit.split() if _bit.isalnum()]
        tag = "".join(_bits)
        tags.append(tag)

    return " #".join(tags)


def import_class(cl):
    d = cl.rfind(".")
    class_name = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [class_name])
    return getattr(m, class_name)