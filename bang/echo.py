import sys
import logging

# configure loggers
log_formatter = logging.Formatter('%(message)s')

stdout = logging.getLogger('echo.stdout')
stdout.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(stream=sys.stdout)
log_handler.setFormatter(log_formatter)
stdout.addHandler(log_handler)

stderr = logging.getLogger('echo.stderr')
stderr.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(stream=sys.stderr)
log_handler.setFormatter(log_formatter)
stderr.addHandler(log_handler)

quiet = False

def exception(e):
    '''
    print an exception message to stderr
    '''
    global quiet
    if quiet: return

    stderr.exception(e)

def err(format_msg, *args, **kwargs):
    '''print format_msg to stderr'''
    global quiet
    if quiet: return

    stderr.info(format_msg.format(*args, **kwargs))

def out(format_msg, *args, **kwargs):
    '''
    print format_msg to stdout, taking into account verbosity level
    '''
    global quiet
    if quiet: return

    stdout.info(format_msg.format(*args, **kwargs))

