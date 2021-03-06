# -*- coding: utf-8 -*-
'''
Base: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
'''

__version__ = '0.0.3'

import os
import sys
import time
import atexit
from signal import SIGTERM

from single_access import lock


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        #~ os.chdir('/') 
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        lock_file = lock(self.pidfile)
        if not lock_file:
            sys.stderr.write('Can\'t lock file: %s\n' % self.pidfile)
            sys.exit(1)
        atexit.register(self.delpid)
        lock_file.truncate()
        lock_file.write('%i' % os.getpid())
        lock_file.flush()

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def delpid(self):
        os.unlink(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        lock_file = lock(self.pidfile)
        if not lock_file:
            sys.stderr.write('Daemon already running\n')
            sys.exit(1)
        # Start the daemon
        lock_file.close()
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        if not os.path.isfile(self.pidfile):
            sys.stderr.write('Daemon not running\n')
            return

        lock_file = lock(self.pidfile)
        if lock_file:
            lock_file.close()
            sys.stderr.write('Daemon not running\n')
            return

        try:
            pid = int(open(self.pidfile).read())
        except ValueError:
            sys.stderr.write('Can\'t stop daemon, bad value in file: %s\n' % 
                self.pidfile)
            return

        # Try killing the daemon process	
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.unlink(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
