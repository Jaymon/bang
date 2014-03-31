# Bang

A static site generator, powers [marcyes.com](http://marcyes.com)

You run bang from the command line:

    $ bang command --project-dir=...

-------------------------------------------------------------------------------

## 1 minute getting started

First, install bang:

    $ pip install bang

Make a new project:

    $ bang generate --project-dir=~/bang-quickstart

Then compile your new project:

    $ bang compile --project-dir=~/bang-quickstart

And start up the development server to take a look at your new project:

    $ bang serve --project-dir=~/bang-quickstart

Now, open a browser and load `localhost:8000` to see your masterpiece, that's it!

-------------------------------------------------------------------------------

## Setup and Configuration

A bang site can have any folder structure and bang will check each folder for a markdown (extension `.md`) file, if it finds one named `index.md` it will not treat it like a blog post but just compile the folder to an `index.html` file. If it finds a markdown file with any other name, then it is considered a blog post with the file's name being the title. So, it basically uses this structure for its posts, so if you have this file structure:

    project-dir/
      input/
        2014/
          001-this-is-the-slug/
            This is the title of the blog post.md

It would compile down to a blog post with a title *This is the title of the blog post* available at the uri:

    /2014/001-this-is-the-slug

Any other files (images or whatnot) will just be copied over to their respective locations.

Bang can be configured using environment variables, basically, any `BANG_*` environment variables wil be put into the configuration, here are a couple you might want to set:

**BANG_HOST** -- the host of your website, this is used to generate urls and stuff.

**BANG_METHOD** -- the http method to use (either `http` or `https`).

-------------------------------------------------------------------------------

## Project directory

Your project directory is where all the magic happens. It has to contain a few folders:

### input (required)

This is where all your blog posts go.

### template (required)

This is where all your [Jinja](http://jinja.pocoo.org/) templates go, they are used to compile your blog posts to their final form.

### output (optional)

This is the default output directory when the `compile` command is used with no `--output-dir` argument.

### bangfile.py (optional)

You can add this file to configure bang when compiling:

```python
# /project_dir/bangfile.py
name = "your site name"
description = "your site description"
host = "example.com"
```

-------------------------------------------------------------------------------

## Plugins

bang includes a couple built-in plugins that you can include in your config.py file, to activate them per site:

```python
# /project_dir/config.py

from bang.plugins import sitemap # to automatically generate a sitemap.xml file

from bang.plugins import feed # generate an rss feed at host/feed.rss for the last 10 posts
```

That's it, once they are imported they will run when they need to.

-------------------------------------------------------------------------------

## Commands

### compile

Use this to compile your `project-dir/input` directory to the final form in the `output-dir` directory.

Compile your site using the default output directory:

    $ bang compile --project-dir=...

That will place the compiled output to `project-dir/output`, you can also move the output directory to another location:

    $ bang compile --project-dir=... --output-dir=...

### serve

Use this to fire up a local server so you can see your compiled site. You can set the port with the `--port` flag.

    $ bang server --project-dir=... --port=8000

### watch

This is designed to be used on the remote server that will host your site in a cron job, it will try and pull down the code using a git repo, if there are changes, then it will compile the new changes, since it is run in cron, you should include the full path:

    $ /usr/local/bin/bang watch --project-dir=...

### generate

Generate a site skeleton that you can use as a starting point to your own bang site, this will take the `project_dir` and make sure it exists (or create it) and then add `input` and `template` dirs along with skeleton template files.

    $ bang generate --project-dir=...

-------------------------------------------------------------------------------

## Events

Events are callbacks that are fired at specific times.

The easiest way to hook these in to your site compiling is to define or import them into your `bangfile.py` configuration file. You can see examples of how they are used in the `bang.plugins` [module](https://github.com/Jaymon/bang/tree/master/bang/plugins).

Events are basically defined like this:

```python
from .. import event, echo

def callback(event_name, site):
    """print all the post titles and urls to the screen"""
    for p in site.posts:
        echo.out(p.title)
        echo.err(p.url)

event.listen('output.finish', callback)
```

### output.finish

This event is fired after all the posts are compiled, right now it is used to do things like generating RSS feeds and the sitemap.

### dom.[TAGNAME]

This event is fired for every element in a post that matches, so if you wanted to do something with `a` tags, you could hook up a callback to listen on `dom.a`.

```python
from .. import event, echo

def callback(event_name, parent, elem):
    """print all href urls in every a tag"""
    echo.out(elem.href)

event.listen('dom.a', callback)
```

-------------------------------------------------------------------------------

## Install

Use pip:

    pip install bangtext

-------------------------------------------------------------------------------

## License

MIT

-------------------------------------------------------------------------------

## TODO

The folders should allow tagging with #hashtags

a project should be able to include a plugins directory (python module) that will allow customization, there should be events added around all the major things during execution (eg, a post_compiled event, a pre_compile event) that the plugins module the user adds can hook into. Not sure this needed anymore though since you can configure the plugins in your `bangfile.py` file

http://pythonhosted.org/Markdown/extensions/api.html

`index.html` should be changed to `post.html` and `aux.html` to be more flexible.

make an event listening decorator that takes an event name

```
@event.callback('event_name')
def callback(*args, **kwargs):
    pass
```

would `generate` command be better as `start` or `skeleton`?

