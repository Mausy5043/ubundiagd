#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon15.py measures the size of selected logfiles.
# These are all counters, therefore no averaging is needed.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')
os.nice(10)

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    samples = 1
    datapoints = 3

    sampleTime = 60
    cycleTime = samples * sampleTime
    # sync to whole minute
    waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
    if DEBUG:
      print "NOT waiting {0} s.".format(waitTime)
    else:
      time.sleep(waitTime)
    while True:
      startTime = time.time()

      result = do_work().split(',')
      data = map(int, result)

      sampleptr = sampleptr + 1
      if (sampleptr == samples):
        do_report(data)
        sampleptr = 0

      waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
      if (waitTime > 0):
        if DEBUG:print "Waiting {0} s".format(waitTime)
        time.sleep(waitTime)

def do_work():
  # 3 datapoints gathered here
  kernlog=messlog=syslog=0

  if IS_SYSTEMD:
    # -p, --priority=
    #       Filter output by message priorities or priority ranges. Takes either a single numeric or textual log level (i.e.
    #       between 0/"emerg" and 7/"debug"), or a range of numeric/text log levels in the form FROM..TO. The log levels are the
    #       usual syslog log levels as documented in syslog(3), i.e.  "emerg" (0), "alert" (1), "crit" (2), "err" (3),
    #       "warning" (4), "notice" (5), "info" (6), "debug" (7). If a single log level is specified, all messages with this log
    #       level or a lower (hence more important) log level are shown. If a range is specified, all messages within the range
    #       are shown, including both the start and the end value of the range. This will add "PRIORITY=" matches for the
    #       specified priorities.
    kernlog = commands.getoutput("journalctl --since=00:00:00 --no-pager -p 3 |wc -l").split()[0]
    messlog = commands.getoutput("journalctl --since=00:00:00 --no-pager -p 4 |wc -l").split()[0]
    syslog  = commands.getoutput("journalctl --since=00:00:00 --no-pager      |wc -l").split()[0]
  else:
    kernlog = commands.getoutput("wc -l /var/log/kern.log").split()[0]
    messlog = commands.getoutput("wc -l /var/log/smartd.log").split()[0]
    syslog  = commands.getoutput("wc -l /var/log/syslog").split()[0]

  return '{0}, {1}, {2}'.format(kernlog, messlog, syslog)

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

  result = ', '.join(map(str, result))
  flock = '/tmp/ubundiagd/15.lock'
  lock(flock)
  f = file('/tmp/ubundiagd/15-cnt-loglines.csv', 'a')
  f.write('{0}, {1}\n'.format(outDate, result) )
  f.close()
  unlock(flock)
  return

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/ubundiagd/15.pid')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    elif 'foreground' == sys.argv[1]:
      # assist with debugging.
      print "Debug-mode started. Use <Ctrl>+C to stop."
      DEBUG = True
      if DEBUG:
      	logtext = "Daemon logging is ON"
      	syslog.syslog(syslog.LOG_DEBUG, logtext)
      daemon.run()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|restart|foreground" % sys.argv[0]
    sys.exit(2)
