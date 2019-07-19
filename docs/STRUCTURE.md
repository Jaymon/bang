# Structure of the codebase

## Compilation

Create a `bang.Site` instance, the Site instance will create the `bang.config.Config` instance, this Config instance will be used throughout the compilation through different contexts, the contexts are so different parts of the sites can have a bit different configuration.

The idea of context configuration came up because I wanted the site to have `//uri` links throughout the html portion of the site but the RSS feed and sitemap should have `scheme://host/uri` and so the config instance can be manipulated for different contexts but the code basically uses all the same methods and stuff, only the underlying configuration changes depending on what is being compiled.

The config instance defines what types of things are compiled, the different default types are located in `bang.types`. The different types should have an `.output()` method that is responsible for compiling that type to its final state (e.g. the Aux and Post types compile down to html but the Other type just copies the vanilla file to the output directory with no changes). These classes are also where the template file is defined