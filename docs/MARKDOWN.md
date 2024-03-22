# Markdown

Bang uses Markdown version 3.4.3 or greater, you can install it using pip:

    $ pip install Markdown==3.4.3

The [ref](https://github.com/Jaymon/bang/blob/master/bang/data/project/input/ref/index.md) markdown file gives an overview of supported markdown syntax and should always be up to date.


## Quick Overview

For the most part, Bang uses vanilla markdown, but there are some enhancements you can take advantage of if you like:

### Easy Footnotes

Using the `^n` footnote will just assign footnotes in order:

```
first[^n] second[^n]

[^n]: this will be assigned to the "first" footnote
[^n]: this will be assigned to the "second" footnote
```

That way you don't have to worry about uniquely naming footnotes since they are just assigned in order, but if you want to give your footnotes unique names that works also.


### Easy links

Similar to the footnotes, using the `n` reference name:

```
[first][n]
[second][n]

[n]: http://first.com
[n]: http://second.com
```


### Easy images

If no title is used, then the alt becomes the title:

```
![this will be the title](path/to/image.jpg)
```

