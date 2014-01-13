import sys
import os
import argparse
import subprocess

import markdown
from jinja2 import Environment, FileSystemLoader

from server import Server
from path import Directory, ProjectDirectory
from generator import Site


__version__ = "0.0.3"


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
        help='Used with "serve" command, the port for the webserver'
    )
#    parser.add_argument(
#        '--repo', '-r',
#        dest='repo',
#        default='',
#        type=str,
#        help='Used with "watch" command, the git repo to monitor'
#    )
    parser.add_argument("-v", "--version", action='version', version="%(prog)s {}".format(__version__))
    parser.add_argument('command', nargs='?', default="compile", choices=["compile", "serve", "watch"])
    args = parser.parse_args()

    project_dir = ProjectDirectory(args.project_dir)
    output_dir = args.output_dir
    if output_dir:
        output_dir = Directory(output_dir)

    else:
        output_dir = Directory(args.project_dir, 'output')

    if args.command == 'compile':
        s = Site(project_dir, output_dir)
        s.output()

    elif args.command == 'serve':
        s = Server(str(output_dir), args.port)
        s.serve_forever()

    elif args.command == 'watch':
        d = Directory(project_dir, '.git')
        if d.exists():
            try:
                output = subprocess.check_output(["git", "pull", "origin", "master"], stderr=subprocess.STDOUT)
                if output.find("Updating") >= 0:
                    # there are new changes, let's recompile the project
                    s = Site(project_dir, output_dir)
                    s.output()

                elif output.find("Already up-to-date"):
                    # nothing has changed, so don't recompile
                    pass
                else:
                    raise RuntimeError(output)

            except subprocess.CalledProcessError, e:
                raise e
                pass

    return 0


if __name__ == u'__main__':
    sys.exit(console())

