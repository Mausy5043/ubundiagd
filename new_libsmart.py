#!/usr/bin/python

import commands, time

DEBUG = False

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.diskid   = "smartinfo-" + diskid
    self.vars     = "-"
    self.health   = "-"
    self.selftest = "-"
    self.identity = commands.getoutput("cat " + self.diskid + "-i.dat").splitlines()
    retm=retd=rets=""
    for line in self.identity:
      if DEBUG:print line
      if (line != ''):
        ls=line.split()
        if (ls[0] == "Model"):
          retm = line.split(': ')[1].strip()
        if (ls[0] == "Device") and (ls[1] == "Model:"):
          retd = line.split(': ')[1].strip()
        if (ls[0] == "Serial"):
          rets = line.split(': ')[1].strip()
    self.identity = retm + " || " + retd + " (" + rets +")"

  def smart(self):
    self.vars     = commands.getoutput("cat " + self.diskid + "-A.dat").splitlines()
    self.health   = commands.getoutput("cat " + self.diskid + "-H.dat")
    self.selftest = commands.getoutput("cat " + self.diskid + "-l.dat")
    if DEBUG:print self.vars
    return 0

  def getdata(self,id):
    ret=""
    for line in self.vars:
      if (line != ''):
        ls=line.split()
        if (ls[0] == id):
          if DEBUG:print line.split()
          ret=ls[9]
    return ret

  def gethealth(self):
    return self.health[0]

  def getlasttest(self):
    return self.selftest

  def getinfo(self):
    return self.identity

if __name__ == '__main__':

  DEBUG = True

  sda = SmartDisk("wwn-0x4891478331354402817x")
  sda.smart()

  print sda.getdata('194')
  print "last test:"
  print sda.getlasttest()
  print "diskid"
  print sda.getinfo()
  print "health"
  print sda.gethealth()
  print "data 9"
  print sda.getdata('9')
