# Themes

A theme is what your project looks like, bang has a default theme that is used if no theme is specified, you can set your theme using the configuration:

```python
config.theme_name = "THEME_NAME"
```

The [default themes directory](https://github.com/Jaymon/bang/tree/master/bang/data/themes) can be used as an example of how you can structure your own project's `themes` directory.

A theme directory is structured like this:

     themes/
       THEME_NAME/
         input/
         template/
           amp/
             page.html
           page.html
           pages.html


A theme lives in a `themes` directory.

## Input

The `input` directory in a theme's directory is similar to the project's `input` directory, anything in it is copied over to the project's `output` directory.

## Template

The `template` directory is where all your [Jinja](http://jinja.pocoo.org/) templates go, they are used to compile your blog posts to their final form. Bang looks for a few template files by default for blog posts:

* `page.html` - This contains the html for rendering a page's permalink page.
* `pages.html` - This contains the html for rendering a list of pages.
