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

def do_writesample(cnsql, sample):
  sample = sample.split(', ')
  sample_time = sample[0]
  sample_epoch = int(sample[1])
  if (sample[2] == "NaN") or (sample[2] == "nan"):
    print "not storing NAN"
  else:
    temperature = float(sample[2])
    try:
      cursql = cnsql.cursor()
      cmd = ('INSERT INTO temper '
                        '(sample_time, sample_epoch, temperature) '
                        'VALUES (%s, %s, %s)')
      dat = (sample_time, sample_epoch, temperature)
      print cmd,dat
      cursql.execute(cmd, dat)
      cnsql.commit()
      cursql.close()
    except mdb.Error, e:
      print "*** MySQL error"
      print "**** Error {0:d}: {1!s}".format(e.args[0], e.args[1])
      if cursql:    # attempt to close connection to MySQLdb
        print "***** Closing cursor"
        cursql.close()
      print(e.__doc__)

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
    print "MySQL error"
    print "Error {0:d}: {1!s}".format(e.args[0], e.args[1])
    if consql:    # attempt to close connection to MySQLdb
      print "Closing MySQL connection"
      consql.close()
      print "Closed MySQL connection"
    print(e.__doc__)
    raise

  data = cat(infile).splitlines()
  for entry in range(0, len(data)):
    #print data[entry]
    do_writesample(consql,data[entry])
  print data[-1].split(', ')
