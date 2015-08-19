#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon21.py measures the ambient temperature.

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

def do_work():
  lockfile="/tmp/temperv14.lock"
  datafile="/tmp/temperv14.dat"
  # prevent race conditions
  time.sleep(3)
  while os.path.isfile(lockfile):
    if DEBUG:print "lockfile exists. Waiting..."
    # wait while the server has locked the directory
    time.sleep(1)

  # Read the ambient temperature
  if os.path.isfile(datafile):
    Tamb = commands.getoutput("cat /tmp/temperv14.dat")
  else:
    Tamb = "NaN"

  if Tamb > 45:
    if DEBUG:print "*** Ambient temperature too high ***"
    if DEBUG:print Tamb
    Tamb = "NaN"
  if Tamb < 5:
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
      daemon.run()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|restart|foreground" % sys.argv[0]
    sys.exit(2)
