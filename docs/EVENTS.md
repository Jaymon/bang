# Events

Events are callbacks that are fired at specific times. As bang outputs a project it runs various events at certain times.


## Hooking into an event

You can hook into an event using [your bangfile](https://github.com/Jaymon/bang/blob/master/docs/CONFIGURATION.md)

You hook into the event using code like this:

```python
from bang import event

@event("EVENT_NAME")
def callback(event, config):
    pass
```

Every event callback should take an `event` and `config` argument. The `event` argument can have additional values that were passed in when the event was broadcast. The `config` argument contains the current project configuration.

The easiest way to hook these in to your project compiling is to define or import them into your `bangfile.py` configuration file. You can see examples of how they are used in the `bang.plugins` [module](https://github.com/Jaymon/bang/tree/master/bang/plugins).

Events are basically defined like this:

```python
from bang import event

@event("output.finish")
def callback(event, config):
    """print all the page titles and urls to the screen"""
    for p in config.get_type("page":
        print(p.title)
        print(p.url)
```


## Events

This might not be an exhaustive list, the bang output logs will tell you when it is running events so you might be able to find other events that are ran at certain times during compilation and output.


### configure.plugins

This is primarily used by plugins to set default plugin configuration before project configuration so the project configuration can override the plugins configuration.


### configure.project

This is called right after the bangfile is loaded in order to set initial global configuration.


### configure.theme

Use this to set specific theme configuration


### configure.theme.THEME_NAME

If you are testing different themes that have different required configuration you can use this event to separate the configuration as you switch between themes in the `configure.project`


### context.NAME

Anytime the configuration context changes, this event is called, when the html pages are generated, `context.html` is the broadcast event, the feed plugin will broadcast `context.feed` and the sitemap plugin will broadcast `context.sitemap`, the amp plugin will broadcast a `context.amp` event.

```python
from bang import event
from bang.plugins import feed

@event("context.html")
def callback(event, config):
    """allows custom configuration for html context"""
    pass

@event("context.feed")
def callback(event, config):
    """allows custom configuration for feed context"""
    pass
```


### output.template

Fired whenever a template is used


### output.template.page

Fired whenever a template is used on a page type. This is used by plugins to inject html into the template's html.


### output.finish

This event is fired after all the posts are compiled, right now it is used to do things like generating RSS feeds and the sitemap.





