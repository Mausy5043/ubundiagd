#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2016]

# daemon29.py reads winddata from an external weatherstation managed by KNMI.

import syslog, traceback
import os, sys, time, math
from libdaemon import Daemon
import ConfigParser

from urllib2 import Request, urlopen
from bs4 import BeautifulSoup

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "29"
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

    # Start by getting external data.
    EXTERNAL_DATA_EXPIRY_TIME = 5*60 #seconds
    # This decouples the fetching of external data
    # from the reporting cycle.
    result = do_work().split(', ')
    if DEBUG:print "result   :",result
    data.append(map(float, result))
    if (len(data) > samples):data.pop(0)
    extern_time = time.time() + EXTERNAL_DATA_EXPIRY_TIME

    while True:
      try:
        startTime = time.time()

        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)

        # report sample average
        if (startTime % reportTime < sampleTime):   # sync reports to reportTime
          somma = map(sum,zip(*data))
          averages = [format(s / len(data), '.3f') for s in somma]
          if DEBUG:
            logtext = ":   Reporting averages : {0}".format(averages)
            print logtext
            syslog.syslog(syslog.LOG_DEBUG, logtext)

          # only fetch external data if current data is
          # older than EXTERNAL_DATA_EXPIRY_TIME
          if (extern_time < time.time()):
            result = do_work().split(', ')
            if DEBUG:print "result   :",result
            data.append(map(float, result))
            if (len(data) > samples):data.pop(0)
            extern_time = time.time() + EXTERNAL_DATA_EXPIRY_TIME

          #windchill = calc_windchill(float(averages[1]), extern_data[0])
          #avg_ext = [format(s, '.3f') for s in data]
          #avg_ext.append(windchill)
          #if DEBUG:
          #  logtext = ":   Reporting avg_ext : {0}".format(avg_ext)
          #  print logtext
          #  syslog.syslog(syslog.LOG_DEBUG, logtext)

          do_report(averages, flock, fdata)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):                          # sync to sampleTime [s]
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print "Unexpected error:"
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def do_work():
  #set defaults
  ms = 0
  gr = 270

  ardtime=time.time()
  try:
    req = Request("http://xml.buienradar.nl/")
    response = urlopen(req, timeout=25)
    output = response.read()
    soup = BeautifulSoup(output)
    souptime = time.time()-ardtime

    MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
    GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
    #datum = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).datum)
    ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
    gr = GRwind.replace("<"," ").replace(">"," ").split()[1]

    if DEBUG:
      logtext = ":   [do_work]       : {0:.2f} s".format(souptime)
      print logtext
      syslog.syslog(syslog.LOG_DEBUG, logtext)
  except Exception as e:
    logtext = "****** Exception encountered : " + str(e)
    syslog.syslog(syslog.LOG_DEBUG, logtext)
    ardtime = time.time() - ardtime
    logtext = "****** after                 {0:.2f} s".format(ardtime)
    syslog.syslog(syslog.LOG_DEBUG, logtext)

  gilzerijen = '{0}, {1}'.format(ms, gr)
  return gilzerijen

def calc_windchill(T,W):
  # use this data to determine the windchill temperature acc. JAG/TI
  # ref.: http://knmi.nl/bibliotheek/knmipubTR/TR309.pdf
  JagTi = 13.12 + 0.6215 * T - 11.37 * (W * 3.6)**0.16 + 0.3965 * T * (W * 3.6)**0.16
  if (JagTi > T):
    JagTi = T

  return JagTi

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = time.strftime('%Y-%m-%dT%H:%M:%S')
  outEpoch = int(time.strftime('%s'))
  # round to current minute to ease database JOINs
  outEpoch = outEpoch - (outEpoch % 60)
  ardtime = time.time()
  result = ', '.join(map(str, result))
  #ext_result = ', '.join(map(str, ext_result))
  #flock = '/tmp/raspdiagd/23.lock'
  lock(flock)
  f = file(fdata, 'a')
  f.write('{0}, {1}, {2}\n'.format(outDate, outEpoch, result) )
  f.close()
  unlock(flock)
  ardtime = time.time() - ardtime
  if DEBUG:
    logtext = ":   [do_report] : {0}, {1}".format(outDate, result)
    print logtext
    #syslog.syslog(syslog.LOG_DEBUG, logtext)
    logtext = ":   [do_report]       : {0:.2f} s".format(ardtime)
    print logtext
    syslog.syslog(syslog.LOG_DEBUG, logtext)

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
  daemon = MyDaemon('/tmp/' + leaf + '/29.pid')
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
