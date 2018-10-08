

class Base(object):

    def __init__(self):
        self._settings = {}

    def get_settings(self):
        return self._settings

    def set_settings(self, settings):
        self._settings = settings
