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

def do_createtable(cnsql)
  try:
    cursql = cnsql.cursor()
    cmd = ('SOURCE createtable21.sql')
    cursql.execute(cmd)
    cnsql.commit()
    cursql.close()
  except mdb.Error, e:
    print("MySQL error")
    print "Error %d: %s" % (e.args[0],e.args[1])
    if consql:    # attempt to close connection to MySQLdb
      print("Closing MySQL connection")
      consql.close()
      print("Closed MySQL connection")
    print(e.__doc__)
    raise

def do_writesample(cnsql, sample)
  sample = sample.split(', ')
  sample_time = sample[0]
  sample_epoch = int(sample[1])
  temperature = float(sample[2])

  cursql = cnsql.cursor()
  cmd = ('INSERT INTO temper '
                    '(sample_time, sample_epoch, temperature) '
                    'VALUES (%s, %s, %s)')
  if DEBUG: print cmd, "// result = ",result
  dat = (t_sample[0], int(t_sample[1]), result )
  cursql.execute(cmd, dat)
  cnsql.commit()
  cursql.close()

if __name__ == "__main__":
  try:              # Initialise MySQLdb
    consql = mdb.connect(host='sql.lan', db='domotica', read_default_file='~/.my.cnf')

    if consql.open: # Hardware initialised succesfully -> get a cursor on the DB.
      cursql = consql.cursor()
      cursql.execute("SELECT VERSION()")
      versql = cursql.fetchone()
      cursql.close()
      logtext = "{0} : {1}".format("Attached to MySQL server", versql)
      print logtext
  except mdb.Error, e:
    print("MySQL error")
    print "Error %d: %s" % (e.args[0],e.args[1])
    if consql:    # attempt to close connection to MySQLdb
      print("Closing MySQL connection")
      consql.close()
      print("Closed MySQL connection")
    print(e.__doc__)
    raise

  do_createtable(consql)

  data = cat(infile).splitlines()
  print data[-1].split(', ')
  for entry in range(0, len(data)):
    print data[entry]
    #do_writesample(consql,data[entry])
  print data[0].split(', ')
  print data[1].split(', ')
  print data[-1].split(', ')
