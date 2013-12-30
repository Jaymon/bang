import sys
import os
import argparse

import markdown
from jinja2 import Environment, FileSystemLoader

from server import Server
from path import Directory, ProjectDirectory
from generator import Site


__version__ = "0.0.2"


def console():
    '''
    cli hook

    return -- integer -- the exit code
    '''
    parser = argparse.ArgumentParser(description='Bang - Static site generator')
    parser.add_argument(
        '--project-dir', '--dir', '-d',
        dest='project_dir',
        default=os.curdir,
        help='directory, defaults to current working directory'
    )
    parser.add_argument(
        '--output-dir', '-o',
        dest='output_dir',
        default=None,
        help='directory, defaults to project-dir/output'
    )
    parser.add_argument(
        '--port', '-p',
        dest='port',
        default=8000,
        type=int,
        help='the port for serve command'
    )
    parser.add_argument("-v", "--version", action='version', version="%(prog)s {}".format(__version__))
    parser.add_argument('command', nargs='?', default="compile", choices=["compile", "serve"])
    args = parser.parse_args()

    output_dir = args.output_dir
    if output_dir:
        output_dir = Directory(output_dir)
    else:
        output_dir = Directory(args.project_dir, 'output')

    if args.command == 'compile':

        s = Site(ProjectDirectory(args.project_dir), output_dir)
        s.output()

    elif args.command == 'serve':
        s = Server(str(output_dir), args.port)
        s.serve_forever()

    return 0


if __name__ == u'__main__':
    sys.exit(console())

