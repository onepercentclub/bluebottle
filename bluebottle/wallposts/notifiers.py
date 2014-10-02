from django.contrib.sites.models import Site


"""
This should be in utils
"""

class WallPostObserver:

    def __init__(self, instance):

        # the object wall the post is left (project, task...)
        self.post = instance.content_object

        # author of the post
        self.author = instance.author

        self.site = 'https://' + Site.objects.get_current().domain

    def notify(self):
        pass


class ReactionObserver:

    def __init__(self, instance):
        self.reaction = instance
        self.post = instance.wallpost
        self.reaction_author = self.reaction.author
        self.post_author = self.post.author
        self.site = 'https://' + Site.objects.get_current().domain

    def notify(self):
        pass


#Change The name
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
        #can be done better, move this responsibility inside the Observer
        if issubclass(observer, WallPostObserver):
            self._register_wallpost_observer(observer)

        if issubclass(observer, ReactionObserver):
            self._register_reaction_observer(observer)

    def _register_wallpost_observer(self, observer):
        self.wallpost_observer_list.append(observer)

    def _register_reaction_observer(self, observer):
        self.reaction_observer_list.append(observer)

    def notify_wallpost_observers(self, instance):
        for each in self.wallpost_observer_list:
            if isinstance(instance.content_object, each.model):
                observer = each(instance)
                observer.notify()

    def notify_reaction_observers(self, instance):
        for each in self.reaction_observer_list:
            if isinstance(instance.wallpost.content_object, each.model):
                observer = each(instance)
                observer.notify()
