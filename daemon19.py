#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon19.py measures the temperature of the diskarray.

import os, sys, time, math, commands
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
#sdf
#sdg

DEBUG = False

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 7
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		if DEBUG:
			print "NOT waiting {0} s.".format(waitTime)
		else:
			time.sleep(waitTime)
		while True:
			startTime = time.time()

			result = do_work().split(',')
			if DEBUG: print result

			data[sampleptr] = map(float, result)
			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				averages = [format(s / samples, '.3f') for s in somma]
				if DEBUG:print averages
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				if DEBUG:print "Waiting {0} s".format(int(waitTime))
				time.sleep(waitTime)

def do_work():
	# 5 datapoints gathered here
	#
	sda.smart()
	sdb.smart()
	sdc.smart()
	sdd.smart()
	sde.smart()
	#sdf
	#sdg

	# disktemperature
	Tsda=sda.getdata('194')
	Tsdb=sdb.getdata('194')
	Tsdc=sdc.getdata('194')
	Tsdd=sdd.getdata('194')
	Tsde=sde.getdata('194')
	Tsdf=0
	Tsdg=0

	if DEBUG: print Tsda, Tsdb, Tsdc, Tsdd, Tsde
	return '{0}, {1}, {2}, {3}, {4}'.format(Tsda, Tsdb, Tsdc, Tsdd, Tsde)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	result = ', '.join(map(str, result))
	flock = '/tmp/ubundiagd/19.lock'
	lock(flock)
	f = file('/tmp/ubundiagd/19-tempdisk.csv', 'a')
	# write out a NaN for disks sdf and sdg
	f.write('{0}, {1}, NaN, NaN\n'.format(outDate, result) )
	f.close()
	unlock(flock)
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/ubundiagd/19.pid')
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
