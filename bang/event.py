
events = {}

def listen(event_name, callback):
    global events

    events.setdefault(event_name, [])
    events[event_name].append(callback)


def broadcast(event_name, *args, **kwargs):
    global events

    for callback in events.get(event_name, []):
        callback(event_name, *args, **kwargs)

