#!/usr/bin/env python

# M. Hendrix 20160101

# Feed CSV-data into the MySQL database

import MySQLdb as mdb

infile = "/srv/array1/datastore/boson/21-aux-ambient.csv"

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret


if __name__ == "__main__":
  cat(infile)
  print len(ret)
