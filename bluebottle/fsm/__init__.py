from django.db import models
from django.dispatch import Signal

pre_transition = Signal(providing_args=['instance', 'name', 'source', 'target', 'options', 'kwargs'])
post_transition = Signal(providing_args=['instance', 'name', 'source', 'target', 'options', 'kwargs'])


class TransitionNotAllowed(Exception):
    """Exception that is raised when a transition that is not allowed in the current state
    is tried.
    """


class Transition(object):
    """
    Object that represent FSM transitions

        `source`: A list of sources the transition can start from
        `target`: the target of the transtion
        `method`: the actual transition method
        `conditions`: conditions that need to hold for the transition to be possible
        `options`: extra arguments passed when defining the transition
    """
    def __init__(self, name, source, target, method, conditions=None, options=None):
        self.name = name
        if not isinstance(source, list):
            source = [source]

        self.source = source
        self.target = target
        self.method = method
        self.conditions = conditions or []
        self.options = options or {}

    def is_allowed(self, instance):
        """ Check if the initiative is allowed currently. """
        return all(condition(instance) is None for condition in self.conditions)

    def errors(self, instance):
        """ Errors that prevent the transition """
        for condition in self.conditions:
            error = condition(instance)

            if error:
                if isinstance(error, (list, tuple)):
                    for e in error:
                        yield e
                else:
                    yield error


class FSMFieldDescriptor(object):
    """ Descriptor makes it possible to prevent direct modification of the field """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, type=None):
        """ If called on a class, return the field, so that we can access the
        transition decorator on the field.

        If called on an instance, return the current value
        """
        if instance is None:
            return self.field

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        """
        Prevent modification of the field.
        """
        if self.field.protected and self.field.name in instance.__dict__:
            raise AttributeError('Direct {0} modification is not allowed'.format(self.field.name))

        instance.__dict__[self.field.name] = value


class FSMField(models.CharField):
    """ Model field that prevents direct transitions and exposes a transition decorator. """

    def __init__(self, protected=True, max_length=20, *args, **kwargs):
        self.protected = protected
        self.transitions = []
        super(FSMField, self).__init__(max_length=max_length, *args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """ Add several fields to the model class.

        Make sure `model.<field>` is an FSMFieldDescriptor

        expose _transition_to that makes it possible to change the field
        expose get_all_transitions. This returns all transitions for the currenct value
        expose get_available_transitions. This returns all transitions where the conditions hold

        """
        super(FSMField, self).contribute_to_class(cls, name, **kwargs)
        self.name = name
        descriptor = FSMFieldDescriptor(self)
        setattr(cls, self.name, descriptor)

        def transition_to(instance, value):
            instance.__dict__[self.name] = value

        setattr(cls, '_transition_{}_to'.format(self.name), transition_to)

        def get_available_transitions(instance):
            return self.get_available_transitions(instance)

        setattr(cls, 'get_available_{}_transitions'.format(self.name), get_available_transitions)

        def get_all_transitions(instance):
            return self.get_all_transitions(instance)

        setattr(cls, 'get_all_{}_transitions'.format(self.name), get_all_transitions)

    def get_all_transitions(self, instance):
        return [
            transition for transition in self.transitions
            if '*' in transition.source or getattr(instance, self.name) in transition.source
        ]

    def get_available_transitions(self, instance):
        return [
            transition for transition in self.get_all_transitions(instance) if
            transition.is_allowed(instance)
        ]

    def transition(field, source, target, conditions=None, **kwargs):
        """ Decorator that creates transition functions

        Example:

        class Example(models.model):
            status = FSMField()

            @status.transition(
                source='new'
                target='test'
            )
            def test(self):
                pass


        """
        def inner_transition(func):
            # Store the transition on the field
            transition = Transition(
                func.__name__, source, target, func, conditions, kwargs
            )
            field.transitions.append(transition)

            def do_transition(self, **kwargs):
                original_source = getattr(self, field.name)  # Keep current status so we can revert

                if not transition.is_allowed(self):
                    # The transition is not currently possible
                    raise TransitionNotAllowed(
                        'Not allowed to transition from {} to {}'.format(
                            original_source, target
                        )
                    )

                # Trigger pre_transition (still with the old value
                pre_transition.send(
                    sender=self.__class__,
                    instance=self,
                    name=transition.name,
                    source=transition.source,
                    target=transition.target,
                    options=transition.options,
                    **kwargs
                )

                # Update the value
                getattr(self, '_transition_{}_to'.format(field.name))(target)

                try:
                    func(self)
                    post_transition.send(
                        sender=self.__class__,
                        instance=self,
                        name=transition.name,
                        source=transition.source,
                        target=transition.target,
                        options=transition.options,
                        **kwargs
                    )
                except Exception:
                    # the transition failed. Revert the value
                    getattr(self, '_transition_{}_to'.format(field.name))(original_source)
                    raise

            return do_transition

        return inner_transition
