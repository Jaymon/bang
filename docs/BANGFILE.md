# Project Configuration

## Project Bangfile

The project's `bangfile.py` is an optional file that handles all the configuration for your project, your bangfile will allow you to hook into various events and activate plugins

You can take a look at [the default project bangfile](https://github.com/Jaymon/bang/blob/master/bang/data/project/bangfile.py) to see the basic setup and organization of a bangfile.

Most of your project configuration will be done through setting callbacks on various events, you do that by importing the event handler and binding an event name to your callback, which will be called at various times while bang is compiling your project.

You can also import plugins into your bangfile which will activate those plugins, for example, to turn your project into a blog, in your bangfile you would import the [blog plugin](https://github.com/Jaymon/bang/blob/master/bang/plugins/blog.py):

```python
from bang.plugins import blog
```


## Environment configuration

You can also combine a bangfile with the environment, this allows you to customize your project even further:

```python
# /project_dir/bangfile.py
import os

from bang import event

@event("configure.project")
def configure(event_name, conf):

    conf.name = "your site name"
    conf.description = "your site description"

    # change the host and scheme based on the environment
    env = os.environ.get("BANG_ENV", "prod")
    if env == "prod":
        conf.host = "example.com"
        conf.scheme = "https"
    else:
        conf.host = "localhost"
        conf.scheme = "http"
```


