#!/usr/bin/env python

# M. Hendrix 20160101

# Feed CSV-data into the MySQL database

import MySQLdb as mdb
import os

infile = "/srv/array1/datastore/boson/21-aux-ambient.csv"

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret


if __name__ == "__main__":
  data = cat(infile).splitlines()
  print data[-1].split(', ')
  for entry in range(0, len(data)):
    print data[entry]
  print data[0]
  print data[1]
  print data[-1]
  print data[len(data)]
