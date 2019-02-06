class TokenAuthenticationError(Exception):
    """
    There was an error trying to authenticate with token.
    """
    def __init__(self, value=None):
        self.value = value if value else 'Error trying to authenticate by token'

    def __str__(self):
        return repr(self.value)
