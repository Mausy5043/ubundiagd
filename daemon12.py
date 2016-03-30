#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon12.py measures the CPU load.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import ConfigParser

DEBUG = False
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "12"
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
    raw = [0] * 16

    while True:
      try:
        startTime = time.time()

        result,raw = do_work(raw)
        result     = result.split(',')
        if DEBUG:print result
        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)

        # report sample average
        if (startTime % reportTime < sampleTime):
          somma = map(sum,zip(*data))
          # not all entries should be float
          # 0.37, 0.18, 0.17, 4, 143, 32147, 3, 4, 93, 0, 0
          averages = [format(s / len(data), '.3f') for s in somma]
          averages[3]=int(data[-1][3])
          averages[4]=int(data[-1][4])
          averages[5]=int(data[-1][5])
          if DEBUG:print averages
          do_report(averages, flock, fdata)

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
    with open(filename,'r') as f:
      ret = f.read().strip('\n')
  return ret

def do_work(stat1):
  # 6 datapoints gathered here
  outHistLoad = cat("/proc/loadavg").replace(" ",", ").replace("/",", ")

  with open('/proc/stat', 'r') as f:
    stat2 = f.readlines()[0].split()
  # ref: https://www.kernel.org/doc/Documentation/filesystems/proc.txt
  # -1 "cpu"
  #  0 user: normal processes executing in user mode    0
  #  1 nice: niced processes executing in user mode     +0
  #  2 system: processes executing in kernel mode       1
  #  3 idle: twiddling thumbs                           2
  #  4 iowait: waiting for I/O to complete              3
  #  5 irq: servicing interrupts                        +3
  #  6 softirq: servicing softirqs                      +3
  #  7 steal: involuntary wait                          +3
  #  8 guest: running a normal guest                    +1
  #  9 guest_nice: running a niced guest                +1

  stat2 = map(int, stat2[1:])
  diff0 = [x - y for x, y in zip(stat2, stat1)]
  sum0 = sum(diff0)
  perc = [x / float(sum0) * 100. for x in diff0]

  outCpuUS      = perc[0] + perc[1] + perc[8] + perc[9]
  outCpuSY      = perc[2]
  outCpuID      = perc[3]
  outCpuWA      = perc[4] + perc[5] + perc[6] + perc[7]
  outCpuST = 0   # with the above code this may be omitted.

  return ('{0}, {1}, {2}, {3}, {4}, {5}'.format(outHistLoad, outCpuUS, outCpuSY, outCpuID, outCpuWA, outCpuST), stat2)

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  lock(flock)
  with open(fdata, 'a') as f:
    f.write('{0}, {1}\n'.format(outDate, result) )
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
    if line:
      syslog.syslog(syslog.LOG_ALERT,line)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/' + leaf + '/12.pid')
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
    print "usage: {0!s} start|stop|restart|foreground".format(sys.argv[0])
    sys.exit(2)
