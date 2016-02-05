#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon14.py measures the memory usage.
# These are all counters, therefore no averaging is needed.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import ConfigParser

DEBUG = False
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "14"
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
        data = map(int, result)

        if (startTime % reportTime < sampleTime):
          do_report(data, flock, fdata)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print "Unexpected error:"
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret

def do_work():
  # 8 datapoints gathered here
  # memory /proc/meminfo
  # total = MemTotal
  # free = MemFree - (Buffers + Cached)
  # inUse = (MemTotal - MemFree) - (Buffers + Cached)
  # swaptotal = SwapTotal
  # swapUse = SwapTotal - SwapFree
  # ref: http://thoughtsbyclayg.blogspot.nl/2008/09/display-free-memory-on-linux-ubuntu.html
  # ref: http://serverfault.com/questions/85470/meaning-of-the-buffers-cache-line-in-the-output-of-free

  out = cat("/proc/meminfo").splitlines()
  for line in range(0,len(out)-1):
    mem = out[line].split()
    if mem[0] == 'MemFree:':
      outMemFree = int(mem[1])
    elif mem[0] == 'MemTotal:':
      outMemTotal = int(mem[1])
    elif mem[0] == 'Buffers:':
      outMemBuf = int(mem[1])
    elif mem[0] == 'Cached:':
      outMemCache = int(mem[1])
    elif mem[0] == 'SwapTotal:':
      outMemSwapTotal = int(mem[1])
    elif mem[0] == "SwapFree:":
      outMemSwapFree = int(mem[1])

  outMemUsed = outMemTotal - (outMemFree + outMemBuf + outMemCache)
  outMemSwapUsed = outMemSwapTotal - outMemSwapFree

  return '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}'.format(outMemTotal, outMemUsed, outMemBuf, outMemCache, outMemFree, outMemSwapTotal, outMemSwapFree, outMemSwapUsed)

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  lock(flock)
  f = file(fdata, 'a')
  f.write('{0}, {1}\n'.format(outDate, result) )
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
  daemon = MyDaemon('/tmp/' + leaf + '/14.pid')
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
