from . import echo

events = {}

def bind(event_name, *event_names):
    """decorator that wraps the listen() method to make it easier to bind functions
    to an event"""
    def wrap(callback):
        listen(event_name, callback)
        for en in event_names:
            listen(en, callback)

        return callback

    return wrap


def listen(event_name, callback):
    global events

    events.setdefault(event_name, [])
    events[event_name].append(callback)


def broadcast(event_name, *args, **kwargs):
    global events

    callbacks = events.get(event_name, [])
    echo.out("broadcast event {} to {} callbacks", event_name, len(callbacks))

    for callback in callbacks:
        callback(event_name, *args, **kwargs)


