#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon19.py measures the temperature of the diskarray.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
from libsmart2 import SmartDisk

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda = SmartDisk("wwn-0x50026b723c0d6dd5") # was 0x13230455334254301185x"
sdb = SmartDisk("wwn-0x50014ee261020fce") # was 0x7914297948508409858x"
sdc = SmartDisk("wwn-0x50014ee605a043e2") # was 0x1138954418312597505x"
sdd = SmartDisk("wwn-0x50014ee6055a237b") # was 0x4891478331354402817x"
sde = SmartDisk("wwn-0x50014ee60507b79c") # was 0x2556643098891800577x"
#sda = SmartDisk("wwn-0x7914297948508409858x")
#sdb = SmartDisk("wwn-0x1138954418312597505x")
#sdc = SmartDisk("wwn-0x4891478331354402817x")
#sdd = SmartDisk("wwn-0x2556643098891800577x")
#sde = SmartDisk("wwn-0x13230455334254301185x")
#sdf
#sdg

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    cycles = 6
    SamplesPerCycle = 5
    samples = SamplesPerCycle * cycles

    datapoints = 4
    data = []

    sampleTime = 60
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

        result = do_work().split(',')
        if DEBUG: print result

        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)
        sampleptr = sampleptr + 1

        # report sample average
        if (sampleptr % SamplesPerCycle == 0):
          somma = map(sum,zip(*data))
          averages = [format(s / len(data), '.3f') for s in somma]
          if DEBUG:print averages
          do_report(averages)
          if (sampleptr == samples):
            sampleptr = 0

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(int(waitTime))
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

def do_work():
  # 5 datapoints gathered here
  #
  sda.smart()
  sdb.smart()
  sdc.smart()
  sdd.smart()
  sde.smart()
  #sdf
  #sdg

  # disktemperature
  Tsda=sda.getdata('194')
  Tsdb=sdb.getdata('194')
  Tsdc=sdc.getdata('194')
  Tsdd=sdd.getdata('194')
  Tsde=sde.getdata('194')
  Tsdf=0
  Tsdg=0

  if DEBUG: print Tsda, Tsdb, Tsdc, Tsdd, Tsde
  return '{0}, {1}, {2}, {3}, {4}'.format(Tsda, Tsdb, Tsdc, Tsdd, Tsde)

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  flock = '/tmp/ubundiagd/19.lock'
  lock(flock)
  f = file('/tmp/ubundiagd/19-tempdisk.csv', 'a')
  # write out a NaN for disks sdf and sdg
  f.write('{0}, {1}, NaN, NaN\n'.format(outDate, result) )
  f.close()
  unlock(flock)
  return

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/ubundiagd/19.pid')
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
