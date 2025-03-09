#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import argparse
import subprocess
import os
from collections import defaultdict
import logging
import logging.config
import time

from datatypes import PathServer

from bang import __version__, Project
from bang.path import Dirpath, DataDirpath
from bang.utils import Profiler


logger = logging.getLogger(__name__)


def console_compile(args, project_dir, output_dir):
    with Profiler() as total:
        s = Project(project_dir, output_dir)

        with Profiler() as compile_total:
            s.compile()

        with Profiler() as output_total:
            s.output()

    logger.info("Compiling done in {}".format(compile_total))
    logger.info("Outputting done in {}".format(output_total))
    logger.info("Compile done in {}".format(total))
    return 0


def console_generate(args, project_dir, output_dir):
    logger.info("Generating new project in {}".format(project_dir))
    with Profiler() as total:

        data_d = DataDirpath()
        data_d.project_dir().copy_to(project_dir)

    logger.info("Generate done in {}".format(total))
    return 0


def console_serve(args, project_dir, output_dir):
    with Profiler() as total:
        ret_code = 0
        logger.info("* " * 40)
        logger.info("serving directory")
        logger.info("")
        logger.info("    {}".format(output_dir))
        logger.info("")
        logger.info("at url")
        logger.info("")
        logger.info("    http://localhost:{}".format(args.port))
        logger.info("")
        logger.info("* " * 40)
        s = PathServer(output_dir, server_address=("", args.port))
        try:
            s.serve_forever()

        except KeyboardInterrupt:
            s.server_close()

    logger.info("serve done in {}".format(total))
    return ret_code


def console_test(args, project_dir, output_dir):
    os.environ.setdefault("BANG_ENV", "test")

    console_compile(args, project_dir, output_dir)
    console_serve(args, project_dir, output_dir)


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
            # Don't want to disable existing loggers (like endpoints) that
            # exist before this config is loaded.
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
    parser = argparse.ArgumentParser(
        description="Bang - Static site generator"
    )
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
        help=''.join(
            "Selectively turn off:"
            " [D]ebug, [I]nfo, [W]arning, [E]rror, or [C]ritical,"
            " (--quiet=DI means suppress Debug and Info),"
            " use - to invert"
            " (--quiet=-E means suppress everything but Error)"
        )
    )

    subparsers = parser.add_subparsers(dest="command", help="a sub command")

    compile_parser = subparsers.add_parser(
        "compile",
        parents=[parent_parser],
        help="Compile your site",
        add_help=False
    )
    compile_parser.set_defaults(func=console_compile)

    serve_parser = subparsers.add_parser(
        "serve",
        parents=[parent_parser],
        help="Serve your site",
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

    generate_parser = subparsers.add_parser(
        "generate",
        parents=[parent_parser],
        help=(
            "Generate a skeleton site that is a"
            " great starting point to customize"
        ),
        add_help=False
    )
    generate_parser.set_defaults(func=console_generate)

    test_parser = subparsers.add_parser(
        "test",
        parents=[serve_parser],
        help="Compile and serve a project",
        add_help=False,
        conflict_handler="resolve",
    )
    test_parser.set_defaults(regex=None)
    test_parser.set_defaults(func=console_test)

    args = parser.parse_args()

    if "func" in args:
        project_dir = Dirpath(args.project_dir)
        output_dir = args.output_dir
        if output_dir:
            output_dir = Dirpath(output_dir)

        else:
            output_dir = Dirpath(args.project_dir, 'output')

        ret_code = args.func(args, project_dir, output_dir)

    else:
        # https://stackoverflow.com/questions/4042452/
        parser.print_help()
        ret_code = 0

    sys.exit(ret_code)


if __name__ == "__main__":
    console()

