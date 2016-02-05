#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon19.py measures the temperature of the diskarray.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import ConfigParser
from libsmart2 import SmartDisk

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!

sda = SmartDisk("wwn-0x50026b723c0d6dd5") # SSD 50026B723C0D6DD5"
sdb = SmartDisk("wwn-0x50014ee261020fce") # WD-WCC4N5PF96KD"
sdc = SmartDisk("wwn-0x50014ee605a043e2") # WD-WMC4N0K01249"
sdd = SmartDisk("wwn-0x50014ee6055a237b") # WD-WMC4N0J6Y6LW"
sde = SmartDisk("wwn-0x50014ee60507b79c") # WD-WMC4N0E24DVU"
#sdf
#sdg

DEBUG = False
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "19"
    home = os.path.expanduser('~')
    s = iniconf.read(home + '/' + leaf + '/config.ini')
    if DEBUG: print "config file : ", s
    if DEBUG: print iniconf.items(inisection)
    reportTime = iniconf.getint(inisection, "reporttime")
    cycles = iniconf.getint(inisection, "cycles")
    samplesperCycle = iniconf.getint(inisection, "samplespercycle")
    flock = iniconf.get(inisection, "lockfile")
    fdata = iniconf.get(inisection, "resultfile")

    samples = samplesperCycle * cycles              # total number of samples averaged
    sampleTime = reportTime/samplesperCycle         # time [s] between samples
    cycleTime = samples * sampleTime                # time [s] per cycle

    data = []                                       # array for holding sampledata

    while True:
      try:
        startTime = time.time()

        result = do_work().split(',')
        if DEBUG: print result

        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)

        # report sample average
        if (startTime % reportTime < sampleTime):
          somma = map(sum,zip(*data))
          averages = [format(s / len(data), '.3f') for s in somma]
          if DEBUG:print averages
          do_report(averages, flock, fdata)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(int(waitTime))
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print "Unexpected error:"
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

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

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  lock(flock)
  f = file(fdata, 'a')
  # write out a NaN for disks sdf and sdg
  f.write('{0}, {1}, NaN, NaN\n'.format(outDate, result) )
  f.close()
  unlock(flock)

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

def syslog_trace(trace):
  # Log a python stack trace to syslog
  log_lines = trace.split('\n')
  for line in log_lines:
    if len(line):
      syslog.syslog(syslog.LOG_ALERT,line)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/' + leaf + '/19.pid')
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
