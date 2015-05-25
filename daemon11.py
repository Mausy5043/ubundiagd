#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon11.py measures the CPU temperature.

import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 2
		data = range(samples)

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

			result = do_work()
			data[sampleptr] = int(result)

			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = sum(data[:])
				averages = somma / samples
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				if DEBUG:print "Waiting {0} s".format(waitTime)
				time.sleep(waitTime)

def do_work():
	# Read the CPU temperature
  list = commands.getoutput("sensors").splitlines()
  outTemp = list[17].split()[1].decode('ascii','ignore').replace('C','')

  # Read the Motherboard temperature
  outMBTemp = list[16].split()[1].decode('ascii','ignore').replace('C','')

	return  '{0}, {1}'.format(outTemp, outMBTemp)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	flock = '/tmp/ubundiagd/11.lock'
	lock(flock)
	f = file('/tmp/ubundiagd/11-t-cpu.csv', 'a')
	f.write('{0}, {1}\n'.format(outDate, float(float(result)/1000)) )
	f.close()
	unlock(flock)
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/ubundiagd/11.pid')
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
