from builtins import object
from builtins import str
from collections import Iterable
from functools import partial

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible

from bluebottle.fsm.state import TransitionNotPossible


@python_2_unicode_compatible
class Effect(object):
    post_save = False
    conditions = []
    display = True
    do_not_call_in_templates = True

    @classmethod
    def render(cls, effects):
        context = {
            'opts': effects[0].instance.__class__._meta,
            'effects': effects
        }
        return render_to_string(cls.template, context)

    @property
    def description(self):
        return str(self)

    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.options = kwargs

    def __reduce__(self):
        return (partial(Effect, self.instance, **self.options), ())

    def __eq__(self, other):
        return self.instance == other.instance and type(self) == type(other)

    def pre_save(self, **kwargs):
        pass

    @property
    def is_valid(self):
        return all(condition(self) for condition in self.conditions)

    def __str__(self):
        return self.__class__.__name__

    def to_html(self):
        return str(self)


class BaseTransitionEffect(Effect):
    field = 'states'
    title = _('Change the status')
    template = 'admin/transition_effect.html'

    @property
    def description(self):
        return 'Change status of {} to {}'.format(
            str(self.instance), self.transition.target.name
        )

    @property
    def machine(self):
        return getattr(self.instance, self.field)

    @property
    def is_valid(self):
        return (
            super().is_valid and
            self.transition in self.machine.possible_transitions()
        )

    def pre_save(self, **kwargs):
        try:
            self.transition.execute(self.machine)
        except TransitionNotPossible:
            pass

    def __eq__(self, other):
        return (
            isinstance(other, BaseTransitionEffect) and
            self.transition == other.transition and
            self.instance == other.instance
        )

    def __repr__(self):
        return '<Effect: {}>'.format(self.transition)

    def __str__(self):
        if self.instance:
            return _('{transition} {object}').format(
                transition=self.transition.name,
                object=str(self.instance)
            )
        return str(self.transition.target)

    @ property
    def help(self):
        return _('{}: {}').format(self.instance.__class__._meta.verbose_name, self.instance)

    def to_html(self):
        if self.conditions:
            return _('{transition} {object} if {conditions}').format(
                transition=self.transition.name,
                object=str(self.instance),
                conditions=" and ".join([c.__doc__ for c in self.conditions])
            )
        return _('{transition} {object}').format(
            transition=self.transition.name,
            object=str(self.instance)
        )


def TransitionEffect(transition, field='states', conditions=None, post_save=False, display=True):
    _transition = transition
    _field = field
    _conditions = conditions
    _post_save = post_save
    _display = display

    class _TransitionEffect(BaseTransitionEffect):
        transition = _transition
        field = _field
        conditions = _conditions or []
        post_save = _post_save
        display = _display

    return _TransitionEffect


class BaseRelatedTransitionEffect(Effect):
    post_save = True
    display = False
    description = None
    transition_effect_class = None

    def __init__(self, *args, **kwargs):
        super(BaseRelatedTransitionEffect, self).__init__(*args, **kwargs)
        self.executed = False
        relation = getattr(self.instance, self.relation, [])

        try:
            self.instances = list(relation.all())
        except ValueError:
            self.instances = []
        except AttributeError:
            if isinstance(relation, Iterable):
                self.instances = relation
            else:
                self.instances = [relation]

    def pre_save(self, effects):
        for instance in self.instances:
            if instance:
                effect = self.transition_effect_class(
                    instance, parent=self.instance, **self.options
                )

                if effect not in effects and effect.is_valid and self.transition in effect.machine.transitions.values():
                    self.executed = True
                    effect.pre_save(effects=effects)
                    effects.append(effect)

                instance.execute_triggers(effects=effects)

    def post_save(self):
        if self.executed:
            for instance in self.instances:
                instance.save()

    def __str__(self):
        if self.description:
            return self.description
        return _('{transition} related {object}').format(
            transition=self.transition_effect_class.transition.name,
            object=self.relation
        )

    def __repr__(self):
        return '<Related Transition Effect: {} on {}>'.format(self.transition, list(self.instances))

    def to_html(self):
        if self.conditions:
            return _('{transition} related {object} if {conditions}').format(
                transition=self.transition_effect_class.transition.name,
                object=str(self.relation),
                conditions=" and ".join([c.__doc__ for c in self.conditions])
            )
        return str(self)


def RelatedTransitionEffect(
    _relation, transition, field='states', conditions=None, description=None, display=True
):
    _transition = transition
    _conditions = conditions or []
    _transition_effect_class = TransitionEffect(transition, field, display=display)
    _description = description

    class _RelatedTransitionEffect(BaseRelatedTransitionEffect):
        transition_effect_class = _transition_effect_class
        relation = _relation
        transition = _transition
        conditions = _conditions
        description = _description
        field = 'states'

    return _RelatedTransitionEffect
