#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon21.py measures the ambient temperature.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import ConfigParser

DEBUG = False
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "21"
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

        result = do_work()
        if DEBUG:print result
        if result != "NaN":
          # We can't handle NaNs so we skip those. Otherwise append to the array.
          data.append(float(result))
          if (len(data) > samples):data.pop(0)

        if (startTime % reportTime < sampleTime):
          if DEBUG:print data
          if (len(data) > 0):
            averages = sum(data[:]) / len(data)
            if DEBUG:print averages
            if math.isnan(averages):
              if DEBUG: print "not reporting NAN"
              #time.sleep(1)
            else:
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
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret

def do_work():
  lockfile="/tmp/" + leaf + "/temperv14.lock"
  datafile="/tmp/" + leaf + "/temperv14.dat"
  # We assume success and re-set flag on failure.
  succes = True
  # Prevent race conditions. Give `temperv14` some time to do its thing.
  time.sleep(3)
  while os.path.isfile(lockfile):
    logmessage = "lockfile (" + lockfile+ ") already exists. Waiting..."
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    # wait while the server-app has locked the directory
    time.sleep(1)

  # Read the ambient temperature from the file
  if os.path.isfile(datafile):
    if os.stat(datafile).st_size > 0:
      Tamb = float(cat(datafile))
    else:
      succes = False
      logmessage = "That's odd... datafile has NULL-size!"
      # make something up
      Tamb = 43.210
      if DEBUG:
        print logmessage
        syslog.syslog(syslog.LOG_INFO,logmessage)
  else:
    succes = False
    logmessage = "Datafile ("+ datafile +") has vanished!"
    # make something up
    Tamb = 43.210
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_ALERT,logmessage)

  if (Tamb > 45.0) and succes:
    logmessage = "*** Ambient temperature too high *** ({0!s})".format((Tamb))
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    succes = False
  if (Tamb < 5.0) and succes:
    logmessage = "*** Ambient temperature too low *** ({0!s})".format((Tamb))
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    succes = False

  if (succes == False):Tamb = "NaN"

  return  Tamb

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = time.strftime('%Y-%m-%dT%H:%M:%S')
  outEpoch = int(time.strftime('%s'))
  # round to current minute to ease database JOINs
  outEpoch = outEpoch - (outEpoch % 60)
  lock(flock)
  f = file(fdata, 'a')
  f.write('{0}, {1}, {2:.2f}\n'.format(outDate, outEpoch, result) )
  f.close()
  unlock(flock)

  # t_sample=outDate.split(',')
  # cursql = cnsql.cursor()
  # cmd = ('INSERT INTO temper '
  #                   '(sample_time, sample_epoch, temperature) '
  #                   'VALUES (%s, %s, %s)')
  # if DEBUG: print cmd, "// result = ",result
  # dat = (t_sample[0], int(t_sample[1]), result )
  # cursql.execute(cmd, dat)
  # cnsql.commit()
  # cursql.close()

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
  daemon = MyDaemon('/tmp/' + leaf + '/21.pid')
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
