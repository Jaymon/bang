#!/usr/bin/env python
# -*- coding: utf-8 -*-import os
import sys
import argparse
import subprocess
import os
from collections import defaultdict
import logging
import logging.config
import time

from bang import __version__
from bang.server import Server
from bang.path import Directory, ProjectDirectory
from bang.generator import Site
from bang.skeleton import Skeleton


logger = logging.getLogger(__name__)


def console_compile(args, project_dir, output_dir):
    start = time.time()

    regex = args.regex
    if regex:
        logger.info("Compiling directories matching {} in {} to {}".format(
            regex,
            project_dir.input_dir,
            output_dir
        ))
    else:
        logger.info("Compiling directory {} to {}".format(project_dir.input_dir, output_dir))

    s = Site(project_dir, output_dir)
    s.output(regex)

    stop = time.time()
    multiplier = 1000.00
    rnd = 2
    elapsed = round(abs(stop - start) * float(multiplier), rnd)
    total = "{:.1f} ms".format(elapsed)

    logger.info("Compile done in {}".format(total))
    return 0


def console_generate(args, project_dir, output_dir):
    logger.info("Generating new project in {}".format(project_dir))
    s = Skeleton(project_dir)
    s.output()
    logger.info("generate done")
    return 0


def console_serve(args, project_dir, output_dir):
    ret_code = 0
    logger.info("* " * 40)
    logger.info("serving directory")
    logger.info("serving directory")
    logger.info("")
    logger.info("    {}".format(output_dir))
    logger.info("")
    logger.info("at url")
    logger.info("")
    logger.info("    http://localhost:{}".format(args.port))
    logger.info("")
    logger.info("* " * 40)
    s = Server(str(output_dir), args.port)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass

    logger.info("serve done")
    return ret_code


def console_watch(args, project_dir, output_dir):
    ret_code = 0
    logger.info("running watch")
    d = Directory(project_dir, '.git')
    if d.exists():
        try:
            git_path = subprocess.check_output(['which', 'git']).strip()
            output = subprocess.check_output(
                [git_path, "pull", "origin", "master"],
                stderr=subprocess.STDOUT,
                cwd=str(project_dir)
            )
            if (output.find("Updating") >= 0) or not output_dir.exists():
                # there are new changes, let's recompile the project
                s = Site(project_dir, output_dir)
                s.output()

            elif output.find("Already up-to-date"):
                # nothing has changed, so don't recompile
                pass
            else:
                raise RuntimeError(output)

        except subprocess.CalledProcessError as e:
            raise

    else:
        ret_code = 1

    logger.info("watch done")
    return ret_code


def configure_logging(val):

    if val.startswith("-"):
        # if we had a subtract, then just remove those from being suppressed
        # so -E would only show errors
        levels = val[1:]
    else:
        levels = "".join(set("DIWEC") - set(val.upper()))

    #pout.v(levels)

    class LevelFilter(object):
        def __init__(self, levels):
            self.levels = levels.upper()
            #self.__level = level
            self.__level = logging.NOTSET
        def filter(self, logRecord):
            #pout.v(self.levels)
            return logRecord.levelname[0].upper() in self.levels
            #return logRecord.levelno <= self.__level

    try:
        # https://docs.python.org/2/library/logging.html
        # https://docs.python.org/2/library/logging.config.html#logging-config-dictschema
        # https://docs.python.org/2/howto/logging.html
        # http://stackoverflow.com/questions/8162419/python-logging-specific-level-only
        d = {
            'version': 1,
            'formatters': {
                'basic': {
                    #'format': '[%(levelname).1s|%(filename)s:%(lineno)s] %(message)s',
                    'format': '[%(levelname).1s] %(message)s',
                },
                'message': {
                    'format': '%(message)s'
                }
            },
            'handlers': {
                'stdout': {
                    'level': 'NOTSET',
                    'class': 'logging.StreamHandler',
                    'formatter': 'basic',
                    'filters': ['stdout', 'user'],
                    'stream': 'ext://sys.stdout'
                },
                'stderr': {
                    'level': 'WARNING',
                    'class': 'logging.StreamHandler',
                    'formatter': 'basic',
                    'filters': ['stderr', 'user'],
                    'stream': 'ext://sys.stderr'
                },
            },
            'filters': {
                'stdout': {
                    '()': LevelFilter,
                    'levels': 'DI',
                },
                'stderr': {
                    '()': LevelFilter,
                    'levels': 'WEC',
                },
                'user': {
                    '()': LevelFilter,
                    'levels': levels,
                },
            },
            'root': {
                'level': 'NOTSET',
                'handlers': ['stdout', 'stderr'],
            },
            'incremental': False,
            # Don't want to disable existing loggers (like endpoints) that exist
            # before this config is loaded.
            'disable_existing_loggers': False,
        }
        logging.config.dictConfig(d)

#         logger.debug("debug")
#         logger.info("info")
#         logger.warning("warning")
#         logger.error("error")
#         logger.critical("critical")

    except Exception as e:
        raise

    return val


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    # this is the main parser that will do the actual parsing of arguments
    #parser = argparse.ArgumentParser(description="Bang - Static site generator", add_help=False)
    parser = argparse.ArgumentParser(description="Bang - Static site generator")
    parser.add_argument(
        "-v", "-V", "--version",
        action='version',
        version="%(prog)s {}".format(__version__)
    )
    #parser.add_argument("--quiet", action='store_true', dest='quiet')

    # this is the common base parser for all the command parsers
    #parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument(
        '--project-dir', '--dir', '-d',
        dest='project_dir',
        default=os.curdir,
        help='directory, defaults to current working directory'
    )
    parent_parser.add_argument(
        '--output-dir', '-o',
        dest='output_dir',
        default=None,
        help='directory, defaults to project-dir/output'
    )
    parent_parser.add_argument(
        '--quiet',
        nargs='?',
        const='DIWEC',
        default='',
        type=configure_logging,
        help=''.join([
            'Selectively turn off [D]ebug, [I]nfo, [W]arning, [E]rror, or [C]ritical, ',
            '(--quiet=DI means suppress Debug and Info), ',
            'use - to invert (--quiet=-E means suppress everything but Error)',
        ])
    )

    subparsers = parser.add_subparsers(dest="command", help="a sub command")

    compile_parser = subparsers.add_parser(
        "compile",
        parents=[parent_parser],
        help="compile your site",
        add_help=False
    )
    compile_parser.add_argument(
        '--pattern', '--regex',
        dest="regex",
        required=False,
        help='Only directories matching this pattern will be compiled'
    )
    compile_parser.set_defaults(func=console_compile)

    serve_parser = subparsers.add_parser(
        "serve",
        parents=[parent_parser],
        help="serve your site",
        add_help=False
    )
    serve_parser.add_argument(
        '--port', '-p',
        dest='port',
        default=8000,
        type=int,
        help='The port for the webserver'
    )
    serve_parser.set_defaults(func=console_serve)

    watch_parser = subparsers.add_parser(
        "watch",
        parents=[parent_parser],
        help="Watch for changes in a repo",
        add_help=False
    )
    watch_parser.set_defaults(func=console_watch)

    generate_parser = subparsers.add_parser(
        "generate",
        parents=[parent_parser],
        help="Generate a skeleton site that is a great starting point to customize",
        add_help=False
    )
    generate_parser.set_defaults(func=console_generate)

    args = parser.parse_args()

    project_dir = ProjectDirectory(args.project_dir)
    output_dir = args.output_dir
    if output_dir:
        output_dir = Directory(output_dir)

    else:
        output_dir = Directory(args.project_dir, 'output')

    ret_code = args.func(args, project_dir, output_dir)
    sys.exit(ret_code)


if __name__ == "__main__":
    console()

