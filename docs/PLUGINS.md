# Plugins

Plugins should be imported in your project's `bangfile.py` which will activate them.

You can see the [default plugins here](https://github.com/Jaymon/bang/blob/master/bang/plugins)


## Amp

The amp plugin will create Google Amp pages for each page.

```python
from bang.plugins import amp
```


## Blog

The blog plugin converts your project into a blog

```python
from bang.plugins import blog
```

Blog posts are created using the same folder structure as vanilla bang but the markdown file names become the title

If bang finds a markdown file with any other name than `index.md`, then it is considered a blog post with the file's name being the title. So, if you have this file structure:

    project-dir/
      input/
        2014/
          001-this-is-the-slug/
            This is the title of the blog post.md

It would compile down to a blog post with a title *This is the title of the blog post* available at the uri:

    /2014/001-this-is-the-slug

Any other files (images or whatnot) will just be copied over to their respective locations.


## favicon

This plugin will look for `favicon*` images in the root directory and generate the appropriate html in the head to support them.

```python
from bang.plugins import favicon
```


## feed

This plugin generates a `/feed.rss` RSS file of the found pages. When used with the blog plugin it only generates a feed of blog posts.

```python
from bang.plugins import feed
```


## Google Analytics

This plugin will add GA tracking code, it requires you to configure `config.ga_tracking_id`

```python
from bang.plugins import googleanalytics
```

and you could configure it like this:

```python
from bang import event
from bang.plugins import googleanalytics

@event("configure.project")
def configure(event, config):
	config.ga_tracking_id = "XX-DDDDDDDD-D"
```


## Open Graph

This plugin will add open graph information to your pages.

```python
from bang.plugins import opengraph
```


## Sitemap

This plugin will create a `/sitemap.xml` file of your project's pages.

```python
from bang.plugins import sitemap
```


## Breadcrumbs

This plugin will create a list of pages (e.g., `types.Page` and `bang.plugins.blog.Post` instances) that are in each folder, it creates `index.html` files in the folders so it should be run after any plugins that also generate `index.html` files automatically (like the _blog_ plugin). 

```python
from bang.plugins import breadcrumbs
```

This plugin will check your current theme for a `breadcrumbs.html` template file, otherwise it will fallback to its default template.