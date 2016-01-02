#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon21.py measures the ambient temperature.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import MySQLdb as mdb

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    try:              # Initialise MySQLdb
      consql = mdb.connect(host='sql.lan', db='domotica', read_default_file='~/.my.cnf')

      if consql.open: # Hardware initialised succesfully -> get a cursor on the DB.
        cursql = consql.cursor()
        cursql.execute("SELECT VERSION()")
        versql = cursql.fetchone()
        cursql.close()
        logtext = "{0} : {1}".format("Attached to MySQL server", versql)
        syslog.syslog(syslog.LOG_INFO, logtext)
    except mdb.Error, e:
      if DEBUG:
        print("Unexpected MySQL error")
        print "Error %d: %s" % (e.args[0],e.args[1])
      if consql:    # attempt to close connection to MySQLdb
        if DEBUG:print("Closing MySQL connection")
        consql.close()
        syslog.syslog(syslog.LOG_ALERT,"Closed MySQL connection")
      syslog.syslog(syslog.LOG_ALERT,e.__doc__)
      syslog_trace(traceback.format_exc())
      raise

    reportTime = 180                                # time [s] between reports
    cycles = 1                                      # number of cycles to aggregate
    samplesperCycle = 1                             # total number of samples in each cycle
    samples = samplesperCycle * cycles              # total number of samples averaged
    sampleTime = reportTime/samplesperCycle         # time [s] between samples
    cycleTime = samples * sampleTime                # time [s] per cycle

    data = []                                       # array for holding sampledata

    while True:
      try:
        startTime = time.time()

        result = do_work()
        if DEBUG:print result

        data.append(float(result))
        if (len(data) > samples):data.pop(0)

        if (startTime % reportTime < sampleTime):
          if DEBUG:print data
          averages = sum(data[:]) / len(data)
          if DEBUG:print averages
          if (averages == "NaN") or (averages == "nan"):
            if DEBUG: print "not reporting NAN"
            time.sleep(1)
          else:
            do_report(averages, consql)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print("Unexpected error:")
          print e.message
        # attempt to close connection to MySQLdb
        if consql:
          if DEBUG:print("Closing MySQL connection")
          consql.close()
          syslog.syslog(syslog.LOG_ALERT,"Closed MySQL connection")
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
  succes = True
  time.sleep(3)
  while os.path.isfile(lockfile):
    logmessage = "lockfile exists. Waiting..."
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    # wait while the server has locked the directory
    time.sleep(1)

  # Read the ambient temperature
  if os.path.isfile(datafile):
    if os.stat(datafile).st_size > 0:
      Tamb = float(cat(datafile))
    else:
      succes = False
      logmessage = "datafile has NULL-size"
      if DEBUG:print logmessage
      syslog.syslog(syslog.LOG_INFO,logmessage)
  else:
    succes = False
    logmessage = "datafile doesn't exist"
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)

  if (Tamb > 45.0) and succes:
    logmessage = "*** Ambient temperature too high *** (%s)" % (Tamb)
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    succes = False
  if (Tamb < 5.0) and succes:
    logmessage = "*** Ambient temperature too low *** (%s)" % (Tamb)
    if DEBUG:print logmessage
    syslog.syslog(syslog.LOG_INFO,logmessage)
    succes = False

  if succes = False: Tamb = "NaN"

  return  Tamb

def do_report(result, cnsql):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = time.strftime('%Y-%m-%dT%H:%M:%S, %s')
  flock = '/tmp/ubundiagd/21.lock'
  lock(flock)
  f = file('/tmp/ubundiagd/21-aux-ambient.csv', 'a')
  f.write('{0}, {1}\n'.format(outDate, result) )
  f.close()
  unlock(flock)

  t_sample=outDate.split(',')
  cursql = cnsql.cursor()
  cmd = ('INSERT INTO temper '
                    '(sample_time, sample_epoch, temperature) '
                    'VALUES (%s, %s, %s)')
  if DEBUG: print cmd, "// result = ",result
  dat = (t_sample[0], int(t_sample[1]), result )
  cursql.execute(cmd, dat)
  cnsql.commit()
  cursql.close()
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
