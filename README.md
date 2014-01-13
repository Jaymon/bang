# Bang

A static site generator, powers [marcyes.com](http://marcyes.com)

You run bang from the command line:

    $ bang command --project-dir=...


## Setup

A bang site can have any folder structure and bang will check each folder for a markdown (extension `.md`) file, if it finds one named `index.md` it will not treat it like a blog post but just compile the folder to an `index.html` file. If it finds a markdown file with any other name, then it is considered a blog post with the file's name being the title. So, it basically uses this structure for its posts, so if you have this file structure:

    project-dir/
      input/
        2014/
          001-this-is-the-slug/
            This is the title of the blog post.md

It would compile down to a blog post with a title *This is the title of the blog post* available at the uri:

    /2014/001-this-is-the-slug

Any other files (images or whatnot) will just be copied over to their respective locations.

-------------------------------------------------------------------------------

## Project directory

Your project directory is where all the magic happens. It has to contain a few folders:

### input (required)

This is where all your blog posts go.

### template (required)

This is where all your Jinja templates go, they are used to compile your blog posts to their final form.

### output (optional)

This is the default output directory when the `compile` command is used with no `--output-dir` option set.

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

This is designed to be used on the remote server that will host your site in a cron job, it will try and pull down the code using a git repo, if there are changes, then it will compile the new changes.

    $ bang watch --project-dir=...

-------------------------------------------------------------------------------

# TODO

The folders should allow tagging with #hashtags

