#!/usr/bin/python

import commands, time

DEBUG = False

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.diskid   = "/tmp/ubundiagd/smartinfo-" + diskid
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
    return self.health

  def getlasttest(self):
    return self.selftest

  def getinfo(self):
    return self.identity

if __name__ == '__main__':

  DEBUG = True

  print "**** Initialisation ****"
  sda = SmartDisk("wwn-0x4891478331354402817x")
  print " "
  print "**** smart() ****"
  sda.smart()

  print " "
  print "**** getdata(194) ****"
  print sda.getdata('194')

  print " "
  print "**** getlasttest() ****"
  print sda.getlasttest()

  print " "
  print "**** getinfo() ****"
  print sda.getinfo()

  print " "
  print "**** gethealth() ****"
  print sda.gethealth()

  print " "
  print "**** getdata(9) ****"
  print sda.getdata('9')
