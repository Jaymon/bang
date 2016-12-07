#!/usr/bin/env python
# -*- coding: utf-8 -*-import os
import sys
import argparse
import subprocess
import os
from collections import defaultdict

from bang import __version__
from bang.server import Server
from bang.path import Directory, ProjectDirectory
from bang.generator import Site
from bang import echo
from bang.skeleton import Skeleton


def console_compile(args, project_dir, output_dir):
    echo.out("compiling directory {} to {}...", project_dir.input_dir, output_dir)
    s = Site(project_dir, output_dir)
    s.output()
    echo.out("...done")
    return 0


def console_generate(args, project_dir, output_dir):
    echo.out("Generating new project in {}...", project_dir)
    s = Skeleton(project_dir)
    s.output()
    echo.out("...done")
    return 0


def console_serve(args, project_dir, output_dir):
    ret_code = 0
    echo.out("* " * 40)
    echo.out("serving directory")
    echo.out("serving directory")
    echo.out("")
    echo.out("    {}", output_dir)
    echo.out("")
    echo.out("at url")
    echo.out("")
    echo.out("    http://localhost:{}", args.port)
    echo.out("")
    echo.out("* " * 40)
    s = Server(str(output_dir), args.port)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass

    echo.out("...done")
    return ret_code


def console_watch(args, project_dir, output_dir):
    ret_code = 0
    echo.out("running watch...")
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

    echo.out("...done")
    return ret_code


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
    parser.add_argument("--quiet", action='store_true', dest='quiet')

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

    subparsers = parser.add_subparsers(dest="command", help="a sub command")

    compile_parser = subparsers.add_parser(
        "compile",
        parents=[parent_parser],
        help="compile your site",
        add_help=False
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

    echo.quiet = args.quiet

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

