#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon12.py measures the CPU load.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    reportTime = 60                                 # time [s] between reports
    cycles = 3                                      # number of cycles to aggregate
    samplesperCycle = 5                             # total number of samples in each cycle
    samples = samplesperCycle * cycles              # total number of samples averaged
    sampleTime = reportTime/samplesperCycle         # time [s] between samples
    cycleTime = samples * sampleTime                # time [s] per cycle

    data = []                                       # array for holding sampledata

    while True:
      try:
        startTime = time.time()

        result = do_work().split(',')
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
          do_report(averages)

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
  # 6 datapoints gathered here
  outHistLoad = cat("/proc/loadavg").replace(" ",", ").replace("/",", ")

  # 5 datapoints gathered here
  outCpu = commands.getoutput("vmstat 1 2").splitlines()[3].split()
  outCpuUS = outCpu[12]
  outCpuSY = outCpu[13]
  outCpuID = outCpu[14]
  outCpuWA = outCpu[15]
  outCpuST = 0

  return '{0}, {1}, {2}, {3}, {4}, {5}'.format(outHistLoad, outCpuUS, outCpuSY, outCpuID, outCpuWA, outCpuST)

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  flock = '/tmp/ubundiagd/12.lock'
  lock(flock)
  f = file('/tmp/ubundiagd/12-load-cpu.csv', 'a')
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
  daemon = MyDaemon('/tmp/ubundiagd/12.pid')
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
