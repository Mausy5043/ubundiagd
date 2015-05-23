#!/usr/bin/python

import commands, time

DEBUG = False

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.wwn = diskid
    self.smartinfo = ""
    self.lasttime = -1

  def smart(self):
    t1 = time.time()
    # only read the S.M.A.R.T. data if current data is stale
    # data is considered stale if it is older than 4 minutes
    if ((t1 - self.lasttime) > (4*60)):
      self.smartinfo = commands.getoutput("sudo smartctl -A /dev/disk/by-id/" + self.wwn).splitlines()
      self.lasttime = t1
    else:
      if DEBUG:print "Using old data: "
    if DEBUG:print self.smartinfo
    return 0

  def getinfo(self,id):
    for line in self.smartinfo:
      if (line != ''):
        ls=line.split()
        if (ls[0] == id):
          if DEBUG:print line.split()
          print ret=ls[9]
    return ret



if __name__ == '__main__':
  # do something
  #sda="wwn-0x50026b723c0d6dd5"
  #sdb="wwn-0x5000c50050a30da3"
  #sdc="wwn-0x5000c50050a32d4f"
  # sdd="wwn-0x50014ee6055a237b"
  # sde="wwn-0x50014ee60507b79c"

  DEBUG = True

  sda = SmartDisk("wwn-0x50026b723c0d6dd5")
  sda.smart()
  sda.getinfo('194')
