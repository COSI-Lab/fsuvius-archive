'''
Utility to keep track of changes

We interpret a change of state as a "change object"--though there is no
specific description of what that change object is (and this utility does not
care). To refer to every listener, we issue a "token", which represents a point
in time when that listener last synchronized its state. The token None is
special, indicating that there was no previous time (an initially connecting
client). After querying the changes with a given token, that token is
discarded, and a new token is issued--referring to current point in
time--alongside the issued changes since the previous token.

Tokens should be interpreted to be opaque, but (as an implementation detail)
they currently are an incrementing counter. The Changes object provides a map
permitting one to determine the actual (host) time that a token was issued.

As a Changes object does not actually track the real state, its constructor
expects a function that, when called, returns all the appropriate change
objects to bring an initializing client (None token) into a proper state.
Generally, this will consist solely of add/set changes.
'''

import threading

class Changes(object):
    COUNTER = 1

    @classmethod
    def getToken(cls):
        token = cls.COUNTER
        cls.COUNTER += 1
        return token

    def __init__(self, init_sync):
        self.lock = threading.Lock()
        self.tokens = {}
        self.issue_time = {}
        self.init_sync = init_sync

    def addChange(self, change):
        with self.lock:
            for v in self.tokens.values():
                v.append(change)

    def getChanges(self, token = None):
        with self.lock:
            if token is None or token not in self.tokens:
                result = self.init_sync()
            else:
                result = self.tokens[token]
                del self.tokens[token]
            new_token = self.getToken()
            self.tokens[new_token] = []
            return result
