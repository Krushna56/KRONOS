class AudioBusError(Exception):
    """ Base audio bus exception """

class SubscriberAlreadyExists(AudioBusError):
    """ Raised when a subscriber is already registered """

    pass 

class SubscriberNotFound(AudioBusError):
    pass