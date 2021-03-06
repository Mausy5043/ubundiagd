#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015] (deprecated)

# daemon99.py creates an XML-file on the server.

import syslog, traceback
import os, sys, platform, time, commands
from libdaemon import Daemon
import ConfigParser
from libsmart2 import SmartDisk
import subprocess

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda = SmartDisk("wwn-0x50026b723c0d6dd5") # SSD 50026B723C0D6DD5"
sdb = SmartDisk("wwn-0x50014ee261020fce") # WD-WCC4N5PF96KD"
sdc = SmartDisk("wwn-0x50014ee605a043e2") # WD-WMC4N0K01249"
sdd = SmartDisk("wwn-0x50014ee6055a237b") # WD-WMC4N0J6Y6LW"
sde = SmartDisk("wwn-0x50014ee60507b79c") # WD-WMC4N0E24DVU"

DEBUG = False
leaf = os.path.realpath(__file__).split('/')[-2]

class MyDaemon(Daemon):
  def run(self):
    iniconf = ConfigParser.ConfigParser()
    inisection = "99"
    home = os.path.expanduser('~')
    s = iniconf.read(home + '/' + leaf + '/config.ini')
    if DEBUG: print "config file : ", s
    if DEBUG: print iniconf.items(inisection)
    reportTime = iniconf.getint(inisection, "reporttime")
    cycles = iniconf.getint(inisection, "cycles")
    samplesperCycle = iniconf.getint(inisection, "samplespercycle")
    flock = iniconf.get(inisection, "lockfile")

    samples = samplesperCycle * cycles              # total number of samples averaged
    sampleTime = reportTime/samplesperCycle         # time [s] between samples
    cycleTime = samples * sampleTime                # time [s] per cycle

    myname = os.uname()[1]
    mount_path = '/srv/array1/dataspool/'
    remote_path = mount_path + myname
    remote_lock = remote_path + '/client.lock'

    while True:
      try:
        startTime=time.time()

        if os.path.exists(remote_path):
          do_xml(remote_path)
        else:
          if DEBUG:print remote_path + " not available"

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

def do_xml(rpath):
  #
  #usr             = commands.getoutput("whoami")
  home						= os.path.expanduser('~')
  uname           = os.uname()

  #Tcpu           =
  #fcpu           =

  fi              = home +"/.ubundiagd.branch"
  with open(fi,'r') as f:
    ubundiagdbranch = f.read().strip('\n')

  uptime          = commands.getoutput("uptime")
  dfh             = commands.getoutput("df -h")
  mds             = commands.getoutput("cat /proc/mdstat |awk 'NR<5'")  #FIXME
  freeh           = commands.getoutput("free -h")
  #psout          = commands.getoutput("ps -e -o pcpu,args | cut -c -132 | awk 'NR>2' | sort -nr | head -10 | sed 's/&/\&amp;/g' | sed 's/>/\&gt;/g'")
  p1              = subprocess.Popen(["ps", "-e", "-o", "pcpu,args"], stdout=subprocess.PIPE)
  p2              = subprocess.Popen(["cut", "-c", "-132"], stdin=p1.stdout, stdout=subprocess.PIPE)
  p3              = subprocess.Popen(["awk", "NR>2"], stdin=p2.stdout, stdout=subprocess.PIPE)
  p4              = subprocess.Popen(["sort", "-nr"], stdin=p3.stdout, stdout=subprocess.PIPE)
  p5              = subprocess.Popen(["head", "-10"], stdin=p4.stdout, stdout=subprocess.PIPE)
  p6              = subprocess.Popen(["sed", "s/&/\&amp;/g"], stdin=p5.stdout, stdout=subprocess.PIPE)
  p7              = subprocess.Popen(["sed", "s/>/\&gt;/g"], stdin=p6.stdout, stdout=subprocess.PIPE)
  p8              = subprocess.Popen(["sed", "s/</\&lt;/g"], stdin=p7.stdout, stdout=subprocess.PIPE)
  psout           = p8.stdout.read()

  #
  sda.smart()
  sdb.smart()
  sdc.smart()
  sdd.smart()
  sde.smart()
  RBCsda=sda.getdata('5')
  RBCsdb=sdb.getdata('5')
  RBCsdc=sdc.getdata('5')
  RBCsdd=sdd.getdata('5')
  RBCsde=sde.getdata('5')
  #Tsda=sda.getdata('198')
  OUsdb=sdb.getdata('198')
  OUsdc=sdc.getdata('198')
  OUsdd=sdd.getdata('198')
  OUsde=sde.getdata('198')
  # disktemperature
  Tsda=sda.getdata('194')
  Tsdb=sdb.getdata('194')
  Tsdc=sdc.getdata('194')
  Tsdd=sdd.getdata('194')
  Tsde=sde.getdata('194')
  # disk power-on time
  Pta=sda.getdata('9')
  Ptb=sdb.getdata('9')
  Ptc=sdc.getdata('9')
  Ptd=sdd.getdata('9')
  Pte=sde.getdata('9')
  # disk health
  Hda=sda.gethealth()
  Hdb=sdb.gethealth()
  Hdc=sdc.gethealth()
  Hdd=sdd.gethealth()
  Hde=sde.gethealth()
  # Self-test info
  Testa=sda.getlasttest()
  Testb=sdb.getlasttest()
  Testc=sdc.getlasttest()
  Testd=sdd.getlasttest()
  Teste=sde.getlasttest()
  # Disk info
  Infoa=sda.getinfo()
  Infob=sdb.getinfo()
  Infoc=sdc.getinfo()
  Infod=sdd.getinfo()
  Infoe=sde.getinfo()

  #
  with open(rpath + '/status.xml', 'w') as f:

    f.write('<server>\n')

    f.write('<name>\n')
    f.write(uname[1] + '\n')
    f.write('</name>\n')

    f.write('<df>\n')
    f.write(dfh + '\n')
    f.write('-\n')
    f.write(mds + '\n')
    f.write('</df>\n')

    f.write('<temperature>\n')
    f.write('SSD: ' + Tsda + ' || disk1: ' + Tsdb + ' || disk2: ' + Tsdc + ' || disk3: ' + Tsdd + ' || disk4: ' + Tsde + ' [degC]\n')
    f.write('\n')
    f.write('---SSD---\n')
    f.write(' Name      : ' + Infoa + '\n')
    f.write(' PowerOn   : ' + Pta + '\n')
    #f.write(' Last test : ' + 'Not available\n')
    if not "PASSED" in Hda:
      f.write('             ' + Hda +'\n')
    if not(RBCsda=="0"):
      f.write('              Retired Block Count (5) = ' + RBCsda +'\n')
    f.write('---disk1---\n')
    f.write(' Name      : ' + Infob + '\n')
    f.write(' PowerOn   : ' + Ptb + '\n')
    if not "without" in Testb:
      f.write(' Last test : ' + Testb +'\n')
    if not "PASSED" in Hdb:
      f.write('             ' + Hdb +'\n')
    if not(RBCsdb=="0") or not(OUsdb=="0"):
      f.write('              Retired Block Count (5) = ' + RBCsdb + ' - Offline Uncorrectable (198) = ' + OUsdb +'\n')
    f.write('---disk2---\n')
    f.write(' Name      : ' + Infoc + '\n')
    f.write(' PowerOn   : ' + Ptc + '\n')
    if not "without" in Testc:
      f.write(' Last test : ' + Testc +'\n')
    if not "PASSED" in Hdc:
      f.write('             ' + Hdc +'\n')
    if not(RBCsdc=="0") or not(OUsdc=="0"):
      f.write('              Retired Block Count (5) = ' + RBCsdc + ' - Offline Uncorrectable (198) = ' + OUsdc +'\n')
    f.write('---disk3---\n')
    f.write(' Name      : ' + Infod + '\n')
    f.write(' PowerOn   : ' + Ptd + '\n')
    if not "without" in Testd:
      f.write(' Last test : ' + Testd +'\n')
    if not "PASSED" in Hdd:
      f.write('             ' + Hdd +'\n')
    if not(RBCsdd=="0") or not(OUsdd=="0"):
      f.write('              Retired Block Count (5) = ' + RBCsdd + ' - Offline Uncorrectable (198) = ' + OUsdd +'\n')
    f.write('---disk4---\n')
    f.write(' Name      : ' + Infoe + '\n')
    f.write(' PowerOn   : ' + Pte + '\n')
    if not "without" in Teste:
      f.write(' Last test : ' + Teste +'\n')
    if not "PASSED" in Hde:
      f.write('             ' + Hde +'\n')
    if not(RBCsde=="0") or not(OUsde=="0"):
      f.write('              Retired Block Count (5) = ' + RBCsde + ' - Offline Uncorrectable (198) = ' + OUsde +'\n')
    f.write(' ')
    #f.write(str(Tcpu) + ' degC @ '+ str(fcpu) +' MHz\n')
    f.write('</temperature>\n')

    f.write('<memusage>\n')
    f.write(freeh + '\n')
    f.write('</memusage>\n')

    f.write('<uptime>\n')
    f.write(uptime + '\n')
    f.write(uname[0]+ ' ' +uname[1]+ ' ' +uname[2]+ ' ' +uname[3]+ ' ' +uname[4]+ ' ' +platform.platform() +'\n')
    f.write(' - ubundiagd   on: '+ ubundiagdbranch +'\n')
    f.write('\nTop 10 processes:\n' + psout +'\n')
    f.write('</uptime>\n')

    f.write('</server>\n')

def lock(fname):
  fd = open(fname, 'a').close()

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
  daemon = MyDaemon('/tmp/' + leaf + '/99.pid')
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
