from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from bluebottle.fsm.state import TransitionNotPossible


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
        return unicode(self)

    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.options = kwargs

    def __eq__(self, other):
        return self.instance == other.instance and type(self) == type(other)

    def pre_save(self, **kwargs):
        pass

    @property
    def is_valid(self):
        return True

    def __unicode__(self):
        return self.__class__.__name__

    def to_html(self):
        return unicode(self)


class BaseTransitionEffect(Effect):
    field = 'states'
    title = _('Change the status')
    template = 'admin/transition_effect.html'

    @property
    def description(self):
        return 'Change status of {} to {}'.format(
            unicode(self.instance), self.transition.target.name
        )

    @property
    def machine(self):
        if not self.instance:
            import ipdb
            ipdb.set_trace()
        return getattr(self.instance, self.field)

    @property
    def is_valid(self):
        return (
            all(condition(self) for condition in self.conditions) and
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

    def __unicode__(self):
        return unicode(self.transition.target)

    @property
    def help(self):
        return _('{}: {}').format(self.instance.__class__._meta.verbose_name, self.instance)

    def to_html(self):
        if self.conditions:
            return _('{transition} {object} if {conditions}').format(
                transition=self.transition.name,
                object=unicode(self.instance),
                conditions=" and ".join([c.__doc__ for c in self.conditions])
            )
        return _('{transition} {object}').format(
            transition=self.transition.name,
            object=unicode(self.instance)
        )


def TransitionEffect(transition, field='states', conditions=None, post_save=False):
    _transition = transition
    _field = field
    _conditions = conditions
    _post_save = post_save

    class _TransitionEffect(BaseTransitionEffect):
        transition = _transition
        field = _field
        conditions = _conditions or []
        post_save = _post_save

    return _TransitionEffect


class BaseRelatedTransitionEffect(Effect):
    post_save = True
    display = False

    def __init__(self, *args, **kwargs):
        super(BaseRelatedTransitionEffect, self).__init__(*args, **kwargs)

        relation = getattr(self.instance, self.relation)

        try:
            self.instances = list(relation.all())
        except AttributeError:
            try:
                self.instances = list(relation)
            except TypeError:
                self.instances = [relation]

    @property
    def is_valid(self):
        return all(condition(self) for condition in self.conditions)

    def pre_save(self, effects=None, **kwargs):
        for instance in self.instances:
            effect = self.transition_effect_class(instance)
            if effect not in effects and self.transition in effect.machine.transitions.values():
                effect.pre_save(effects=effects)

                effects.append(effect)

                instance.execute_triggers(effects=effects)
                instance.save()

    def post_save(self):
        for instance in self.instances:
            instance.save()

    def __unicode__(self):
        return '{} related {}'.format(
            self.transition_effect_class.name,
            self.relation
        )

    def __repr__(self):
        return '<Related Transition Effect: {} on {}>'.format(self.transition, list(self.instances))

    def to_html(self):
        if self.conditions:
            return _('{transition} related {object} if {conditions}').format(
                transition=self.transition_effect_class.name,
                object=unicode(self.relation),
                conditions=" and ".join([c.__doc__ for c in self.conditions])
            )
        return _('{transition} related {object}').format(
            transition=self.transition_effect_class.name,
            object=unicode(self.relation)
        )


def RelatedTransitionEffect(_relation, transition, field='states', conditions=None):
    _transition = transition
    _conditions = conditions or []
    _transition_effect_class = TransitionEffect(transition, field)

    class _RelatedTransitionEffect(BaseRelatedTransitionEffect):
        transition_effect_class = _transition_effect_class
        relation = _relation
        transition = _transition
        conditions = _conditions
        field = 'states'

    return _RelatedTransitionEffect
