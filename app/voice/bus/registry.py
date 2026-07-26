from voice.bus.exceptions import (SubscriberAlreadyExists, SubscriberNotFound,)

class SubscriberRegistry:

    def __init__(self):

        self._subscribers = {}

    def add(self, name, worker):

        if name in self._subscribers:
            raise SubscriberAlreadyExists
        
        self._subscribers[name] = worker 

    def remove(self, name):

        if name not in self._subscribers:
            raise SubscriberNotFound(name)
        
        del self._subscribers[name]
    
    def values(self):
        return self._subscribers.values()
    
    def names(self):
        return self._subscribers.keys()
        