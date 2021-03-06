#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

import sys, os, time, atexit, syslog
from signal import SIGTERM

class Daemon:
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
      sys.stderr.write("fork no.1 failed: {0:d} ({1!s})\n".format(e.errno, e.strerror))
      sys.exit(1)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # do second fork
    try:
      pid = os.fork()
      if pid > 0:
        # exit from second parent
        sys.exit(0)
    except OSError, e:
      sys.stderr.write("fork no.2 failed: {0:d} ({1!s})\n".format(e.errno, e.strerror))
      sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(self.stdin, 'r')
    so = open(self.stdout, 'a+')
    se = open(self.stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # write pidfile
    atexit.register(self.delpid)
    pid = str(os.getpid())
    open(self.pidfile,'w+').write("{0!s}\n".format(pid))

  def delpid(self):
    os.remove(self.pidfile)

  def start(self):
    """
    Start the daemon
    """
    # Check for a pidfile to see if the daemon already runs
    try:
      with open(self.pidfile,'r') as pf:
        pid = int(pf.read().strip())
    except IOError:
      pid = None

    if pid:
      message = "pidfile %s already exist. Daemon already running?\n"
      sys.stderr.write(message % self.pidfile)
      sys.exit(1)

    # Start the daemon
    message = "Started process \n"
    sys.stderr.write(message)
    syslog.syslog(message)
    self.daemonize()
    self.run()

  def stop(self):
    """
    Stop the daemon
    """
    # Get the pid from the pidfile
    try:
      with open(self.pidfile,'r') as pf:
        pid = int(pf.read().strip())
    except IOError:
      pid = None

    if not pid:
      message = "pidfile %s does not exist. Daemon not running?\n"
      sys.stderr.write(message % self.pidfile)
      return # not an error in a restart

    # Try killing the daemon process
    try:
      message = "Stopped process \n"
      syslog.syslog(message)
      sys.stderr.write(message)

      while 1:
        os.kill(pid, SIGTERM)
        time.sleep(0.1)

    except OSError, err:
      if err.errno == 3:
        if os.path.exists(self.pidfile):
          os.remove(self.pidfile)
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
