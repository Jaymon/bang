# Bang

A static site generator built in Python with support for things like sitemaps, Open Graph, RSS feeds, and Google Amp. Powers [marcyes.com](http://marcyes.com)

You run bang from the command line:

    $ bang command --project-dir=...

[Documentation](https://github.com/Jaymon/bang/tree/master/docs)

-------------------------------------------------------------------------------

## Installation

Use pip:

    pip install bangtext

-------------------------------------------------------------------------------

## 1 minute getting started

First, install bang:

    $ pip install bangtext

Make a new project:

    $ bang generate --project-dir=~/bang-quickstart

Then compile your new project:

    $ bang compile --project-dir=~/bang-quickstart

And start up the development server to take a look at your new project:

    $ bang serve --project-dir=~/bang-quickstart

Now, open a browser and load `localhost:8000` to see your masterpiece, that's it!

-------------------------------------------------------------------------------

## Setup and Configuration

A bang project will check each folder in the project directory for an `index.md` markdown file, if it finds one it will compile it to an `index.html` file. 

So, if you have this file structure in your `project-dir`:

    project-dir/
      input/
        foo/
        	index.md
        	image.png
        bar/
        	index.md

Would compile down to this file structure:

    project-dir/
      output/
        foo/
        	index.html
        	image.png
        bar/
        	index.html

So it would have urls like:

	http://host.tld/foo/
	http://host.tld/bar/


### Plugins

You activate [plugins](https://github.com/Jaymon/bang/blob/master/docs/PLUGINS.md) by importing them into your [project's bangfile](https://github.com/Jaymon/bang/blob/master/docs/CONFIGURATION.md).

You can customize your project to your needs, like turning it into a blog, adding Google Amp support, and things like that.


### Project Directory

Your project directory is where all the magic happens.

#### Structure


##### input directory (required)

This is where everything you want to be in the final output folder should go, this is where you would place your markdown files and any other files/folders you want your *live* static site to contain.


##### themes directory (optional)

What your site looks like. Read more about [themes](https://github.com/Jaymon/bang/blob/master/docs/THEMES.md) and how to create your own.


##### output directory (optional)

This is the default output directory when the `compile` command is used with no `--output-dir` argument.


##### bangfile.py (optional)

You can add a [bangfile](https://github.com/Jaymon/bang/blob/master/docs/CONFIGURATION.md) to configure your project.


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

Generate a site skeleton that you can use as a starting point to your own bang site, this will take the `project_dir` and make sure it exists (or create it) and then copy over the [default project](https://github.com/Jaymon/bang/tree/master/bang/data/project) structure.

    $ bang generate --project-dir=...


-------------------------------------------------------------------------------

## Testing

If you cloned this repo, you can test out bang by running (from the repo working directory:

    $ python -m bang generate -d /path/to/testsite/
    $ python -m bang compile -d /path/to/testsite/
    $ python -m bang serve -d /path/to/testsite/

You can also run the unit tests:

    $ python -m unittest bang_test


