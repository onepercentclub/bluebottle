from threading import local


class LocalEffects(local):
    def __init__(self):
        self.effects = []
        self.send_messages = True

    def append(self, effect):
        self.effects += [effect]

    def disable_messages(self):
        self.send_messages = False


local_effects = LocalEffects()
