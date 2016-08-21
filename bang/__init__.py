import os
import argparse
import subprocess


from .server import Server
from .path import Directory, ProjectDirectory
from .generator import Site
from . import echo
from . import event
from .skeleton import Skeleton


__version__ = "0.2.6"


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
    #parser.add_argument("--debug", action='store_true', dest='debug')
    parser.add_argument("--quiet", action='store_true', dest='quiet')
    parser.add_argument('command', nargs='?', default="compile", choices=["compile", "serve", "watch", "generate"])
    args = parser.parse_args()

    echo.quiet = args.quiet

    project_dir = ProjectDirectory(args.project_dir)
    output_dir = args.output_dir
    if output_dir:
        output_dir = Directory(output_dir)

    else:
        output_dir = Directory(args.project_dir, 'output')

    if args.command == 'compile':
        echo.out("compiling directory {} to {}...", project_dir.input_dir, output_dir)
        s = Site(project_dir, output_dir)
        s.output()

    if args.command == 'generate':
        echo.out("Generating new project in {}...", project_dir)
        s = Skeleton(project_dir)
        s.output()

    elif args.command == 'serve':
        echo.out("serving directory {} on http://localhost:{}...", output_dir, args.port)
        s = Server(str(output_dir), args.port)
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            pass

    elif args.command == 'watch':
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

            except subprocess.CalledProcessError, e:
                raise e
                pass

    echo.out("...done")
    return 0

