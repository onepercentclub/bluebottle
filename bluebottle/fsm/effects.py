from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string


class Effect(object):
    effects = []
    save = False
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

    def __eq__(self, other):
        return self.instance == other.instance and type(self) == type(other)

    def do(self, post_save, **kwargs):
        if self.is_valid and self.post_save == post_save:
            self.execute(**kwargs)
            if self.save:
                self.instance.save(perform_effects=False)

    def all_effects(self, result=None):
        result = result or []

        if self.is_valid:
            result.append(self)

            for effect in self.effects:
                if effect.is_valid and effect not in result:
                    for sub_effect in effect.all_effects(result):
                        if sub_effect.is_valid and sub_effect not in result:
                            result.append(sub_effect)

        return result

    def execute(self, **kwargs):
        pass

    @property
    def is_valid(self):
        return True

    def __unicode__(self):
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
    def transition(self):
        return self.machine.transitions.get(self.name)

    @property
    def is_valid(self):
        return self.transition and (
            all(condition(self.machine) for condition in self.conditions) and
            self.transition in self.machine.possible_transitions()
        )

    @property
    def effects(self):
        for effect_class in self.transition.effects:
            yield effect_class(self.instance)

    def execute(self, effects=False, **kwargs):
        self.transition.execute(self.machine, effects=effects)

    def __eq__(self, other):
        return (
            isinstance(other, BaseTransitionEffect) and
            self.transition == other.transition and
            self.instance == other.instance
        )

    def __repr__(self):
        return '<Effect: {}>'.format(self.transition)

    def __unicode__(self):
        return str(self.transition.target)

    @property
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


def TransitionEffect(transition_name, field='states', conditions=None, save=False, post_save=False):
    _field = field
    _conditions = conditions
    _save = save
    _post_save = post_save

    class _TransitionEffect(BaseTransitionEffect):
        name = transition_name
        field = _field
        conditions = _conditions or []
        save = _save
        post_save = _post_save

    return _TransitionEffect


class BaseRelatedTransitionEffect(Effect):
    post_save = True
    display = False

    transition_effect_class = None

    @property
    def machine(self):
        return getattr(self.instance, self.field)

    @property
    def is_valid(self):
        return all(condition(self.machine) for condition in self.conditions)

    @property
    def instances(self):
        value = getattr(self.instance, self.relation)

        if value:
            try:
                for instance in value.all():
                    yield instance
            except AttributeError:
                try:
                    for instance in value:
                        yield instance
                except TypeError:
                    yield value

    @property
    def effects(self):
        for instance in self.instances:
            yield self.transition_effect_class(instance)

    def do(self, post_save, **kwargs):
        if self.is_valid and self.post_save == post_save:
            for effect in self.effects:
                effect.do(post_save, **kwargs)

    def all_effects(self, result=None):
        result = super(BaseRelatedTransitionEffect, self).all_effects(result)
        if self.is_valid:
            for effect in self.effects:
                if effect not in result and effect.is_valid:
                    result.append(effect)

        return result

    def __unicode__(self):
        return '{} related {}'.format(
            self.transition_effect_class.name,
            self.relation
        )

    def to_html(self):
        if self.conditions:
            return _('{transition} related {object} if {conditions}').format(
                transition=self.transition_effect_class.name,
                object=str(self.relation),
                conditions=" and ".join([c.__doc__ for c in self.conditions])
            )
        return _('{transition} related {object}').format(
            transition=self.transition_effect_class.name,
            object=str(self.relation)
        )


def RelatedTransitionEffect(_relation, transition_name, field='states', conditions=None):
    _transition_effect_class = TransitionEffect(transition_name, field, save=True, post_save=True)
    _conditions = conditions or []

    class _RelatedTransitionEffect(BaseRelatedTransitionEffect):
        transition_effect_class = _transition_effect_class
        relation = _relation
        conditions = _conditions
        field = 'states'

    return _RelatedTransitionEffect
