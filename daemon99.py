#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon99.py creates an XML-file and uploads data to the server.

import os, sys, shutil, glob, platform, time, commands
from libdaemon import Daemon
from libsmart import SmartDisk

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda = SmartDisk("/dev/disk/by-id/wwn-0x7914297948508409858x",1)
sdb = SmartDisk("/dev/disk/by-id/wwn-0x982717808011923456x",1)
sdc = SmartDisk("/dev/disk/by-id/wwn-0x3264916919181922304x",1)
sdd = SmartDisk("/dev/disk/by-id/wwn-0x2556643098891800577x",1)
sde = SmartDisk("/dev/disk/by-id/wwn-0x13230455334254301185x",1)

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    samples = 1
    #datapoints = 1
    #data = range(samples)

    sampleTime = 60
    cycleTime = samples * sampleTime

    myname = os.uname()[1]
    mount_path = '/srv/array1/dataspool/'
    remote_path = mount_path + myname
    remote_lock = remote_path + '/client.lock'

    # sync to whole minute
    waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
    if DEBUG:
      print "NOT waiting {0} s.".format(waitTime)
    else:
      time.sleep(waitTime)
    while True:
      startTime=time.time()

      if os.path.exists(remote_path):
        do_mv_data(remote_path)
        do_xml(remote_path)
      else:
        if DEBUG:print remote_path + " not available"

      waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
      if (waitTime > 0):
        if DEBUG:print "Waiting {0} s".format(waitTime)
        time.sleep(waitTime)

def do_mv_data(rpath):
  hostlock = rpath + '/host.lock'
  clientlock = rpath + '/client.lock'
  count_internal_locks=1

  # wait 5 seconds for processes to finish
  time.sleep(5)

  while os.path.isfile(hostlock):
    if DEBUG:print "hostlock exists"
    # wait while the server has locked the directory
    time.sleep(1)

  # server already sets the client.lock. Do it anyway.
  lock(clientlock)

  # prevent race conditions
  while os.path.isfile(hostlock):
    if DEBUG:print "hostlock exists. WTF?"
    # wait while the server has locked the directory
    time.sleep(1)

  while (count_internal_locks > 0):
    time.sleep(1)
    count_internal_locks=0
    for file in glob.glob(r'/tmp/ubundiagd/*.lock'):
      count_internal_locks += 1
    if DEBUG:print "{0} internal locks exist".format(count_internal_locks)

  for file in glob.glob(r'/tmp/*.csv'):
    if os.path.isfile(clientlock):
      if not (os.path.isfile(rpath + "/" + os.path.split(file)[1])):
        if DEBUG:print "moving legacy-data " + file
        shutil.move(file, rpath)

  for file in glob.glob(r'/tmp/ubundiagd/*.csv'):
    if os.path.isfile(clientlock):
      if not (os.path.isfile(rpath + "/" + os.path.split(file)[1])):
        if DEBUG:print "moving data " + file
        shutil.move(file, rpath)

  unlock(clientlock)
  if DEBUG:print "unlocked..."
  return

def do_xml(rpath):
  #
  usr              = commands.getoutput("whoami")
  uname           = os.uname()
  #Tcpu            = float(commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp"))/1000
  #fcpu            = float(commands.getoutput("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"))/1000
  ubundiagdbranch = commands.getoutput("cat $HOME/.ubundiagd.branch")
  uptime          = commands.getoutput("uptime")
  dfh             = commands.getoutput("df -h")
  mds              = commands.getoutput("cat /proc/mdstat |awk 'NR<4'")
  freeh           = commands.getoutput("free -h")
  psout           = commands.getoutput("ps -e -o pcpu,args | awk 'NR>2' | sort -nr | head -10 | sed 's/&/\&amp;/g' | sed 's/>/\&gt;/g'")
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
  f = file(rpath + '/status.xml', 'w')

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
  f.write(' Last test : ' + 'Not available\n')
  f.write('             ' + Hda +'\n')
  f.write('              Retired Block Count = ' + RBCsda +'\n')
  f.write('---disk1---\n')
  f.write(' Name      : ' + Infob + '\n')
  f.write(' PowerOn   : ' + Ptb + '\n')
  f.write(' Last test : ' + Testb +'\n')
  f.write('             ' + Hdb +'\n')
  f.write('              Retired Block Count = ' + RBCsdb + ' - Offline Uncorrectable = ' + OUsdb +'\n')
  f.write('---disk2---\n')
  f.write(' Name      : ' + Infoc + '\n')
  f.write(' PowerOn   : ' + Ptc + '\n')
  f.write(' Last test : ' + Testc +'\n')
  f.write('             ' + Hdc +'\n')
  f.write('              Retired Block Count = ' + RBCsde + ' - Offline Uncorrectable = ' + OUsde +'\n')
  f.write('---disk3---\n')
  f.write(' Name      : ' + Infod + '\n')
  f.write(' PowerOn   : ' + Ptd + '\n')
  f.write(' Last test : ' + Testd +'\n')
  f.write('             ' + Hdd +'\n')
  f.write('              Retired Block Count = ' + RBCsde + ' - Offline Uncorrectable = ' + OUsde +'\n')
  f.write('---disk4---\n')
  f.write(' Name      : ' + Infoe + '\n')
  f.write(' PowerOn   : ' + Pte + '\n')
  f.write(' Last test : ' + Teste +'\n')
  f.write('             ' + Hde +'\n')
  f.write('              Retired Block Count = ' + RBCsde + ' - Offline Uncorrectable = ' + OUsde +'\n')
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

  f.close()
  return

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/ubundiagd/99.pid')
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
