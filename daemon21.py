#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon21.py measures the ambient temperature.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    samples = 1
    datapoints = 1
    # 16 samples/hr:
    sampleTime = 60*3
    cycleTime = samples * sampleTime
    # sync to whole minute
    waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
    if DEBUG:
      print "NOT waiting {0} s.".format(waitTime)
    else:
      time.sleep(waitTime)
    while True:
      try:
        startTime = time.time()

        result = do_work()
        if DEBUG:print result
        data = result

        # report sample average
        sampleptr = sampleptr + 1
        if (sampleptr == samples):
          do_report(data)
          sampleptr = 0

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print("Unexpected error:")
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def syslog_trace(trace):
  '''Log a python stack trace to syslog'''
  log_lines = trace.split('\n')
  for line in log_lines:
    if len(line):
      syslog.syslog(syslog.LOG_ALERT,line)

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret

def do_work():
  lockfile="/tmp/ubundiagd/temperv14.lock"
  datafile="/tmp/ubundiagd/temperv14.dat"
  # prevent race conditions
  time.sleep(3)
  while os.path.isfile(lockfile):
    if DEBUG:print "lockfile exists. Waiting..."
    # wait while the server has locked the directory
    time.sleep(1)

  # Read the ambient temperature
  if os.path.isfile(datafile):
    if os.stat(datafile).st_size > 0:
      Tamb = float(cat(datafile))
    else:
      if DEBUG:print "datafile has NULL-size!"
      Tamb = "NaN"
  else:
    if DEBUG:print "datafile doesn't exist!"
    Tamb = "NaN"

  if Tamb > 45.0:
    if DEBUG:print "*** Ambient temperature too high ***"
    if DEBUG:print Tamb
    Tamb = "NaN"
  if Tamb < 5.0:
    if DEBUG:print "*** Ambient temperature too low ***"
    if DEBUG:print Tamb
    Tamb = "NaN"

  return  Tamb

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  #result = ', '.join(map(str, result))
  flock = '/tmp/ubundiagd/21.lock'
  lock(flock)
  f = file('/tmp/ubundiagd/21-aux-ambient.csv', 'a')
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
  daemon = MyDaemon('/tmp/ubundiagd/21.pid')
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
