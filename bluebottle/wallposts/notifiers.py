from bluebottle.clients.utils import tenant_url


class WallpostObserver:

    def __init__(self, instance):

        # the object wall the post is left (project, task...)
        self.post = instance.content_object

        # author of the post
        self.author = instance.author

        self.site = tenant_url()

    def notify(self):
        pass


class ReactionObserver:

    def __init__(self, instance):
        self.reaction = instance
        self.post = instance.wallpost
        self.reaction_author = self.reaction.author
        self.post_author = self.post.author
        self.site = tenant_url()

    def notify(self):
        pass


class ObserversContainer:

    wallpost_observer_list = []
    reaction_observer_list = []

    _instance = None

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ObserversContainer, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def register(self, observer):
        # can be done better, move this responsibility inside the Observer
        if issubclass(observer, WallpostObserver):
            self._register_wallpost_observer(observer)

        if issubclass(observer, ReactionObserver):
            self._register_reaction_observer(observer)

    def notify_wallpost_observers(self, instance):
        return self._notify(instance,
                            self.wallpost_observer_list,
                            instance.content_object)

    def notify_reaction_observers(self, instance):
        return self._notify(instance,
                            self.reaction_observer_list,
                            instance.wallpost.content_object)

    def _register_wallpost_observer(self, observer):
        self.wallpost_observer_list.append(observer)

    def _register_reaction_observer(self, observer):
        self.reaction_observer_list.append(observer)

    def _notify(self, instance, observer_list, instance_model):
        for each in observer_list:
            if isinstance(instance_model, each.model):
                observer = each(instance)
                observer.notify()
