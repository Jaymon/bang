
post_body = u'''
This is the body text.
'''

master_skeleton = u'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{% block title %}{% endblock %}</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />

    {% block description %}{% endblock %}

    <link rel="icon" href="/favicon.ico" type="image/x-icon" sizes="16x16" />
    <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon" />

    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css">

    <!-- For code syntax highlighting, see: http://highlightjs.org -->
    <link rel="stylesheet" href="//yandex.st/highlightjs/8.0/styles/default.min.css">
    <script src="//yandex.st/highlightjs/8.0/highlight.min.js"></script>

    <link rel="stylesheet" href="/assets/app.css" type="text/css" media="screen, projection">
  </head>

  <body>
    <div id="header"></div>

    <div class="body">
        {% block content %}{% endblock %}
    </div>

    <div id="footer"></div>

    <script>
      hljs.initHighlighting()
    </script>
  </body>
</html>
'''

#index_skeleton = u'''{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime("%Y-%m-%d") }}\n'''
single_skeleton = u'''
<!-- Render just the html of the post, both post.html and posts.html use this -->
{% block content %}
  <h1><a href="{{post.url}}">{{ post.title }}</a></h1>

  {{ post.html }}

  <p class="post-meta">
    {{ post.modified.strftime('%b %d %Y') }}
  </p>

{% endblock %}
'''

post_skeleton = u'''
<!-- render a post permalink -->
{% extends "master.html" %}

{% block title %}{{ post.title }}{% endblock %}

{% block description %}
  <meta name="description" content="{{ post.description }}">
  <meta property="og:url" content="{{ post.url }}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{{ post.title }}" />
  <meta property="og:description" content="{{ post.description }}" />
  <meta property="og:image" content="{{ post.image }}" />
{% endblock %}

{% block content %}
  {% include 'single.html' %}
{% endblock %}
'''

posts_skeleton = u'''
<!-- render a group of posts -->
{% extends "master.html" %}

{% block title %}{{ config.title }}{% endblock %}

{% block description %}
<meta name="description" content="{{ config.description }}">
{% endblock %}

{% block content %}
  {% for post in posts.reverse(10) %}
    {% include 'single.html' %}
    <hr>
  {% endfor %}
{% endblock %}

'''

bangfile_skeleton = u'''import os

host = os.environ.get("BANG_HOST", "")
method = os.environ.get("BANG_METHOD", "http")
title = ""
description = ""

# add all the plugins
from bang.plugins import sitemap, feed
'''

file_skeleton = [
    {
        'dir': ("input", "assets"),
        'basename': 'app.css',
        'content': ''
    },
    {
        'dir': ("input", "hello-world"),
        'basename': 'Hello World.md',
        'content': post_body
    },
    {
        'dir': ("template"),
        'basename': 'master.html',
        'content': master_skeleton
    },
    {
        'dir': ("template"),
        'basename': 'post.html',
        'content': post_skeleton
    },
    {
        'dir': ("template"),
        'basename': 'posts.html',
        'content': posts_skeleton
    },
    {
        'dir': ("template"),
        'basename': 'single.html',
        'content': single_skeleton
    },
    {
        'dir': [],
        'basename': 'bangfile.py',
        'content': bangfile_skeleton
    }
]

class Skeleton(object):
    """responsible for generating a skeleton bang site"""
    def __init__(self, project_dir):
        self.project_dir = project_dir

    def output(self):
        self.project_dir.create()
        for file_dict in file_skeleton:
            d = self.project_dir / file_dict['dir']
            d.create()
            d.create_file(file_dict['basename'], file_dict['content'])

