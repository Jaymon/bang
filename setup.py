#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html
from setuptools import setup, find_packages
import re
import os


name = "bang"
with open(os.path.join(name, "__init__.py"), 'rU') as f:
    version = re.search("^__version__\s*=\s*[\'\"]([^\'\"]+)", f.read(), flags=re.I | re.M).group(1)


setup(
    name="{}text".format(name),
    version=version,
    description='A static site generator',
    author='Jay Marcyes',
    author_email='jay@marcyes.com',
    url='http://github.com/jaymon/{}'.format(name),
    packages=[name, '{}.plugins'.format(name)],
    license="MIT",
    install_requires=['Jinja2', 'markdown'],
    classifiers=[ # https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
    ],
    #test_suite = "{}_test".format(name),
    entry_points = {
        'console_scripts': ['{} = {}:console'.format(name, name)]
    }
)
