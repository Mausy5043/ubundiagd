#!/usr/bin/python

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.wwn = diskid

  def smart(self):
    self.smartcmd = "sudo smartctl -A /dev/disk/by-id/" + self.wwn
    if DEBUG:print self.smartcmd
    return "command defined"




if __name__ == '__main__':
  # do something
  sda=wwn-0x50026b723c0d6dd5
  sdb=wwn-0x5000c50050a30da3
  sdc=wwn-0x5000c50050a32d4f
  #sdd=wwn-0x5000c50052c28f7d
  sdd=wwn-0x50014ee6055a237b
  #sde=wwn-0x5000c50050f3630b
  sde=wwn-0x50014ee60507b79c

  DEBUG = True
  info = SmartDisk(sda)
  print info.smart
